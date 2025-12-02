"""
Celery tasks for user management and background operations.
"""
from celery import shared_task
from .services import add_or_update_user, bulk_add_or_update_users
import logging

logger = logging.getLogger(__name__)


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
