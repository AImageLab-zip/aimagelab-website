"""
Celery tasks for the main app
"""
import requests
from requests.auth import HTTPBasicAuth
import json
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging

from .models import Staff, PublicationIRIS, StaffPublicationIRIS, IRISImportLog

logger = logging.getLogger(__name__)

# Lock key for preventing concurrent imports
IRIS_IMPORT_LOCK_KEY = 'iris_import_in_progress'
IRIS_IMPORT_LOCK_TIMEOUT = 3600  # 1 hour timeout


@shared_task(bind=True)
def import_iris_publications(self):
    """
    Import publications from IRIS service for all staff members.
    
    This task:
    1. Fetches all staff members with valid IRIS IDs
    2. For each staff member, retrieves their publications from IRIS API
    3. Creates or updates publications in the database
    4. Links publications to staff members
    5. Downloads PDF attachments if available
    
    Uses a cache-based lock to prevent concurrent executions.
    """
    # Check if import is already running
    if cache.get(IRIS_IMPORT_LOCK_KEY):
        logger.info("IRIS import already in progress, skipping...")
        return {
            'status': 'skipped',
            'message': 'Import already in progress'
        }
    
    # Acquire lock
    cache.set(IRIS_IMPORT_LOCK_KEY, True, IRIS_IMPORT_LOCK_TIMEOUT)
    
    try:
        # Create import log entry
        import_log = IRISImportLog.objects.create(status='running')
        
        logger.info("Starting IRIS publications import...")
        
        stats = {
            'staff_processed': 0,
            'publications_created': 0,
            'publications_updated': 0,
            'links_created': 0,
            'errors': []
        }
        
        # Get all staff members with Codice Fiscale
        staff_members = Staff.objects.filter(
            hidden=False,
            codice_fiscale__isnull=False
        ).exclude(codice_fiscale='')
        
        logger.info(f"Found {staff_members.count()} staff members to process")
        
        for staff in staff_members:
            try:
                logger.info(f"Processing {staff.cognome} {staff.nome} (CF: {staff.codice_fiscale})")
                
                # Fetch publications from IRIS
                result = fetch_staff_publications(staff, import_log)
                
                stats['staff_processed'] += 1
                stats['publications_created'] += result['created']
                stats['publications_updated'] += result['updated']
                stats['links_created'] += result['links_created']
                
                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': stats['staff_processed'],
                        'total': staff_members.count(),
                        'status': f"Processing {staff.cognome}..."
                    }
                )
                
            except Exception as e:
                error_msg = f"Error processing staff {staff.id_iris}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Update import log
        import_log.status = 'completed'
        import_log.completed_at = timezone.now()
        import_log.staff_processed = stats['staff_processed']
        import_log.publications_created = stats['publications_created']
        import_log.publications_updated = stats['publications_updated']
        import_log.links_created = stats['links_created']
        import_log.save()
        
        logger.info(f"IRIS import completed: {stats}")
        
        return {
            'status': 'completed',
            'stats': stats
        }
        
    except Exception as e:
        error_msg = f"IRIS import failed: {str(e)}"
        logger.error(error_msg)
        
        # Update import log with error
        if 'import_log' in locals():
            import_log.status = 'failed'
            import_log.completed_at = timezone.now()
            import_log.error_message = str(e)
            import_log.save()
        
        return {
            'status': 'failed',
            'message': error_msg
        }
        
    finally:
        # Release lock
        cache.delete(IRIS_IMPORT_LOCK_KEY)


def fetch_staff_publications(staff, import_log):
    """
    Fetch publications for a single staff member from IRIS GW REST API.
    Uses Codice Fiscale (CF) directly to query publications.
    
    Args:
        staff: Staff model instance
        import_log: IRISImportLog instance
        
    Returns:
        dict: Statistics about created/updated publications
    """
    stats = {
        'created': 0,
        'updated': 0,
        'links_created': 0
    }
    
    # Set up authentication and headers
    auth = HTTPBasicAuth(settings.IRIS_API_USERNAME, settings.IRIS_API_PASSWORD)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    
    # Optionally fetch and cache person data for IRIS IDs (useful for other integrations)
    if not staff.iris_pid or not staff.iris_id:
        logger.info(f"Caching person data for CF: {staff.codice_fiscale}")
        person_data = fetch_person_by_cf(staff.codice_fiscale, auth)
        
        if person_data:
            # Update staff with IRIS identifiers
            staff.iris_pid = person_data.get('pid', '')
            staff.iris_id = str(person_data.get('id', ''))
            staff.iris_id_ab = person_data.get('idAb', '')
            staff.save()
            logger.info(f"Cached IRIS IDs - PID: {staff.iris_pid}, ID: {staff.iris_id}")
    
    # Fetch publications directly by Codice Fiscale
    api_url = f"{settings.IRIS_API_BASE_URL}/products"
    params = {
        'author.cf': staff.codice_fiscale,
        'pageSize': 500  # Maximum allowed per page
    }
    
    try:
        # Fetch publications JSON from IRIS GW REST API
        logger.info(f"Fetching publications for CF: {staff.codice_fiscale}")
        response = requests.get(api_url, params=params, auth=auth, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # The response structure is: {"count": "X", "page": "1", "resultList": [...]}
        result_list = data.get('resultList', [])
        
        logger.info(f"Found {len(result_list)} publications for CF: {staff.codice_fiscale}")
        
        # Process each publication
        for pub_data in result_list:
            try:
                process_publication_json(pub_data, staff, stats)
            except Exception as e:
                logger.error(f"Error processing publication: {str(e)}")
                
    except requests.RequestException as e:
        logger.error(f"Failed to fetch publications for CF {staff.codice_fiscale}: {str(e)}")
        raise
    
    return stats


@transaction.atomic
def process_publication_json(pub_data, staff, stats):
    """
    Process a single publication from JSON and create/update in database.
    
    Args:
        pub_data: Dictionary containing publication data from GW REST API
        staff: Staff model instance
        stats: Dictionary to update with statistics
    """
    # Extract publication handle (unique identifier)
    handle = pub_data.get('handle', '')
    
    if not handle:
        logger.warning("Publication without handle, skipping")
        return
    
    # Use handle as unique identifier
    # The internal ID is in search.legacyid_i
    internal_id = pub_data.get('search.legacyid_i', '')
    
    # Check if publication exists (use handle as unique identifier)
    publication, created = PublicationIRIS.objects.get_or_create(
        handle=handle,
        defaults={'hidden': False}
    )
    
    if created:
        stats['created'] += 1
        logger.info(f"Created new publication: {handle}")
    else:
        stats['updated'] += 1
        logger.debug(f"Updating publication: {handle}")
    
    # Map API fields to model fields
    # Based on the GW REST API documentation
    publication.titolo = pub_data.get('dc.title', '')[:500] if pub_data.get('dc.title') else ''
    publication.autori = pub_data.get('authors', '')[:1000] if pub_data.get('authors') else ''
    
    # Extract year from dateIssued
    date_issued = pub_data.get('dateIssued', '')
    if date_issued:
        try:
            # dateIssued is in format YYYY-MM-DDTHH:MM:SSZ
            publication.anno = int(date_issued.split('-')[0])
        except (ValueError, IndexError):
            publication.anno = pub_data.get('dateIssued.year')
    
    # Get collection/type information
    collection = pub_data.get('collection', {})
    if isinstance(collection, dict):
        publication.tipo = collection.get('description', '')[:200]
        publication.tipologia = pub_data.get('dc.type.miur', '')[:200]
    
    # Journal information
    journal = pub_data.get('journal', {})
    if isinstance(journal, dict):
        publication.rivista = journal.get('title', '')[:200]
        publication.issn = journal.get('issn', '')[:50]
    
    # Serie information (if available)
    serie = pub_data.get('serie', {})
    if isinstance(serie, dict):
        serie_title = serie.get('title', '')
        if serie_title:
            publication.rivista = serie_title[:200]
    
    # Abstract and description
    publication.abstract = pub_data.get('descriptionAbstractAll', '')
    
    # DOI and identifiers
    publication.doi = pub_data.get('dc.identifier.doi', '')[:200]
    
    # Language
    publication.language = pub_data.get('language', '')[:10]
    
    # URL/Link
    publication.url = pub_data.get('link', '')[:500]
    
    # Citation
    publication.citation = pub_data.get('citation', '')[:1000]
    
    # State/status
    publication.stato = pub_data.get('stato', '')[:100]
    
    # Fulltext presence
    fulltext_presence = pub_data.get('fulltextPresence', '')
    if fulltext_presence:
        publication.fulltext_available = fulltext_presence != 'none'
    
    # Store internal ID if available
    if internal_id:
        publication.id_iris = str(internal_id)
    
    # Citation counts (optional fields)
    citation_count = pub_data.get('citationCount', {})
    if isinstance(citation_count, dict):
        publication.scopus_citations = citation_count.get('scopus', 0)
        publication.wos_citations = citation_count.get('isi', 0)
    
    # Save publication
    publication.save()
    
    # Create/update staff-publication link
    # Position is not available in the new API, set to 0
    link, link_created = StaffPublicationIRIS.objects.update_or_create(
        staff=staff,
        publication=publication,
        defaults={'posizione': 0}
    )
    
    if link_created:
        stats['links_created'] += 1


def fetch_person_by_cf(codice_fiscale, auth):
    """
    Fetch person data from IRIS by Codice Fiscale.
    
    Args:
        codice_fiscale: Italian fiscal code
        auth: HTTPBasicAuth instance
        
    Returns:
        dict: Person data or None if not found
    """
    api_url = f"{settings.IRIS_API_BASE_URL}/people"
    params = {'cf': codice_fiscale}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(api_url, params=params, auth=auth, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # The response is an array, get the first person if available
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict):
            return data
            
        return None
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch person data for CF {codice_fiscale}: {str(e)}")
        return None


def is_import_running():
    """
    Check if an IRIS import is currently running.
    
    Returns:
        bool: True if import is running, False otherwise
    """
    return bool(cache.get(IRIS_IMPORT_LOCK_KEY))
