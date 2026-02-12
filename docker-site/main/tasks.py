"""
Celery tasks for the main app - includes IRIS import and user sync functionality
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

from .models import UserProfile, PublicationIRIS, UserProfilePublicationIRIS, IRISImportLog
from .services import add_or_update_user, bulk_add_or_update_users

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
        
        # Get all user profiles with Codice Fiscale
        user_profiles = UserProfile.objects.filter(
            is_visible=True,
            codice_fiscale__isnull=False
        ).exclude(codice_fiscale='').select_related('user')
        
        logger.info(f"Found {user_profiles.count()} user profiles to process")
        
        for user_profile in user_profiles:
            try:
                logger.info(f"Processing {user_profile.user.get_full_name()} (CF: {user_profile.codice_fiscale})")
                
                # Fetch publications from IRIS
                result = fetch_user_publications(user_profile, import_log)
                
                stats['staff_processed'] += 1
                stats['publications_created'] += result['created']
                stats['publications_updated'] += result['updated']
                stats['links_created'] += result['links_created']
                
                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': stats['staff_processed'],
                        'total': user_profiles.count(),
                        'status': f"Processing {user_profile.user.get_full_name()}..."
                    }
                )
                
            except Exception as e:
                error_msg = f"Error processing user {user_profile.user.username}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Determine final status based on errors
        if stats['errors']:
            # Check if there are authentication errors (401)
            has_auth_error = any('401' in str(err) for err in stats['errors'])
            if has_auth_error or stats['staff_processed'] == 0:
                final_status = 'failed'
            else:
                final_status = 'completed'  # Partial success
        else:
            final_status = 'completed'
        
        # Update import log
        import_log.status = final_status
        import_log.completed_at = timezone.now()
        import_log.staff_processed = stats['staff_processed']
        import_log.publications_created = stats['publications_created']
        import_log.publications_updated = stats['publications_updated']
        import_log.links_created = stats['links_created']
        
        # Store errors if any
        if stats['errors']:
            import_log.error_message = '\n'.join(stats['errors'])
        
        import_log.save()
        
        logger.info(f"IRIS import {final_status}: {stats}")
        
        return {
            'status': final_status,
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


def fetch_user_publications(user_profile, import_log):
    """
    Fetch publications for a single user from IRIS GW REST API.
    Uses Codice Fiscale (CF) directly to query publications.
    
    Args:
        user_profile: UserProfile model instance
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
    if not user_profile.iris_pid or not user_profile.iris_id:
        logger.info(f"Caching person data for CF: {user_profile.codice_fiscale}")
        person_data = fetch_person_by_cf(user_profile.codice_fiscale, auth)
        
        if person_data:
            # Update user_profile with IRIS identifiers
            user_profile.iris_pid = person_data.get('pid', '')
            user_profile.iris_id = str(person_data.get('id', ''))
            user_profile.iris_id_ab = person_data.get('idAb', '')
            user_profile.save()
            logger.info(f"Cached IRIS IDs - PID: {user_profile.iris_pid}, ID: {user_profile.iris_id}")
    
    # Fetch publications directly by Codice Fiscale
    api_url = f"{settings.IRIS_API_BASE_URL}/products"
    params = {
        'author.cf': user_profile.codice_fiscale,
        'pageSize': 500  # Maximum allowed per page
    }
    
    try:
        # Fetch publications JSON from IRIS GW REST API
        logger.info(f"Fetching publications for CF: {user_profile.codice_fiscale}")
        response = requests.get(api_url, params=params, auth=auth, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # The response structure is: {"count": "X", "page": "1", "resultList": [...]}
        result_list = data.get('resultList', [])
        
        logger.info(f"Found {len(result_list)} publications for CF: {user_profile.codice_fiscale}")
        
        # Process each publication
        for pub_data in result_list:
            try:
                process_publication_json(pub_data, user_profile, stats)
            except Exception as e:
                logger.error(f"Error processing publication: {str(e)}")
                
    except requests.RequestException as e:
        logger.error(f"Failed to fetch publications for CF {user_profile.codice_fiscale}: {str(e)}")
        raise
    
    return stats


@transaction.atomic
def process_publication_json(pub_data, user_profile, stats):
    """
    Process a single publication from JSON and create/update in database.
    
    Args:
        pub_data: Dictionary containing publication data from GW REST API
        user_profile: UserProfile model instance
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
    
    # Create/update user-profile-publication link
    # Position is not available in the new API, set to 0
    link, link_created = UserProfilePublicationIRIS.objects.update_or_create(
        user_profile=user_profile,
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


# ============================================================================
# User Management and Sync Tasks
# ============================================================================

@shared_task(bind=True, max_retries=3)
def sync_user_task(self, user_data):
    """
    Celery task to add or update a single user asynchronously.
    
    Args:
        user_data (dict): User data dictionary
        
    Returns:
        dict: Result with user info and status
        
    Example:
        >>> from main.tasks import sync_user_task
        >>> user_data = {
        ...     'username': 'jdoe',
        ...     'email': 'john.doe@example.com',
        ...     'first_name': 'John',
        ...     'last_name': 'Doe',
        ...     'role': 'phd',
        ... }
        >>> result = sync_user_task.delay(user_data)
        >>> print(result.get())
    """
    try:
        user, profile, created = add_or_update_user(user_data)
        
        logger.info(
            f"User {user.username} {'created' if created else 'updated'} successfully"
        )
        
        return {
            'success': True,
            'username': user.username,
            'email': user.email,
            'created': created,
            'message': f"User {'created' if created else 'updated'} successfully"
        }
    except Exception as exc:
        logger.error(f"Error syncing user: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def bulk_sync_users_task(users_data_list):
    """
    Celery task to add or update multiple users in batch.
    
    Args:
        users_data_list (list): List of user data dictionaries
        
    Returns:
        dict: Summary of the operation
        
    Example:
        >>> from main.tasks import bulk_sync_users_task
        >>> users = [
        ...     {'username': 'user1', 'email': 'user1@example.com', 'role': 'phd'},
        ...     {'username': 'user2', 'email': 'user2@example.com', 'role': 'postdoc'},
        ... ]
        >>> result = bulk_sync_users_task.delay(users)
        >>> print(result.get())
    """
    try:
        results = bulk_add_or_update_users(users_data_list)
        
        logger.info(
            f"Bulk sync completed: {results['created_count']} created, "
            f"{results['updated_count']} updated, {results['error_count']} errors"
        )
        
        return {
            'success': True,
            'summary': {
                'created': results['created_count'],
                'updated': results['updated_count'],
                'errors': results['error_count'],
            },
            'details': results
        }
    except Exception as exc:
        logger.error(f"Error in bulk sync: {str(exc)}")
        return {
            'success': False,
            'error': str(exc)
        }


@shared_task
def populate_users_from_ldap():
    """
    Celery task to populate users from LDAP server daily.
    """
    from django.core.management import call_command
    from django.utils import timezone

    try:
        logger.info(f"Starting LDAP user population at {timezone.now()}")
        call_command('populate_from_ldap')
        logger.info("LDAP user population completed successfully")
        return {'success': True, 'message': 'LDAP population completed'}
    except Exception as exc:
        logger.error(f"LDAP population failed: {str(exc)}")
        return {'success': False, 'error': str(exc)}


@shared_task
def sync_users_from_external_source(source_url=None, source_data=None):
    """
    Celery task to sync users from an external source (API, file, etc.).
    
    Args:
        source_url (str, optional): URL to fetch user data from
        source_data (list, optional): Direct user data list
        
    Returns:
        dict: Summary of the synchronization
        
    Example:
        >>> # From data
        >>> result = sync_users_from_external_source.delay(source_data=users_list)
        >>> 
        >>> # From URL (you need to implement the fetch logic)
        >>> result = sync_users_from_external_source.delay(source_url='https://api.example.com/users')
    """
    try:
        if source_data:
            users_data = source_data
        elif source_url:
            # TODO: Implement fetching from external URL
            # import requests
            # response = requests.get(source_url)
            # users_data = response.json()
            logger.warning("Fetching from URL not yet implemented")
            return {'success': False, 'error': 'URL fetching not implemented'}
        else:
            return {'success': False, 'error': 'No data source provided'}
        
        results = bulk_add_or_update_users(users_data)
        
        logger.info(
            f"External sync completed: {results['created_count']} created, "
            f"{results['updated_count']} updated, {results['error_count']} errors"
        )
        
        return {
            'success': True,
            'summary': {
                'created': results['created_count'],
                'updated': results['updated_count'],
                'errors': results['error_count'],
            },
            'details': results
        }
    except Exception as exc:
        logger.error(f"Error syncing from external source: {str(exc)}")
        return {
            'success': False,
            'error': str(exc)
        }
