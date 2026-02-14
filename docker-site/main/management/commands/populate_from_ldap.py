import ldap
import ldap.filter
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from main.models import UserProfile
import logging

logger = logging.getLogger(__name__)


def to_camel_case(s):
    if not s:
        return ''
    return ' '.join(word.capitalize() for word in s.split())

class Command(BaseCommand):
    help = 'Populate the database with users from LDAP server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            default=True,
            help='Update existing users (default: True)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update_existing = options['update_existing']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Connect to LDAP
            self.stdout.write('Connecting to LDAP server...')
            ldap_client = ldap.initialize(settings.LDAP_SERVER_URI)
            ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            
            # Set network timeout to prevent hanging connections
            ldap_client.set_option(ldap.OPT_NETWORK_TIMEOUT, 10.0)
            
            logger.info(f"Connecting to LDAP server: {settings.LDAP_SERVER_URI}")

            # Anonymous bind
            ldap_client.simple_bind_s()
            logger.info("LDAP bind successful")

            # Get members of ailb-srv group (POSIX group uses memberUid)
            self.stdout.write('Finding ailb-srv group members...')
            group_result = ldap_client.search_s(
                'ou=groups,' + settings.LDAP_SEARCH_BASE,
                ldap.SCOPE_SUBTREE,
                '(cn=ailb-srv)', #substitute ailb-srv with new flag saying if displaying user on website or not
                ['memberUid']
            )

            if not group_result:
                self.stdout.write(self.style.ERROR('ailb-srv group not found'))
                return

            group_dn, group_attrs = group_result[0]
            member_uids = group_attrs.get('memberUid', [])
            self.stdout.write(f'Found {len(member_uids)} members in ailb-srv group')

            created_count = 0
            updated_count = 0
            skipped_count = 0
            processed_usernames = set()

            for uid in member_uids:
                try:
                    if isinstance(uid, bytes):
                        uid = uid.decode('utf-8')
                    
                    # Sanitize uid to prevent LDAP injection
                    safe_uid = ldap.filter.escape_filter_chars(uid)
                    logger.debug(f"Processing user with uid: {safe_uid}")

                    groups_result = ldap_client.search_s(
                        settings.LDAP_SEARCH_BASE,
                        ldap.SCOPE_SUBTREE,
                        f"(&(objectClass=posixGroup)(memberUid={safe_uid}))",
                        ["cn"]
                    )


                    if not groups_result:
                        self.stdout.write(self.style.WARNING(f'Groups not found for {uid}'))
                        skipped_count += 1
                        continue

                    # Search for user by uid (using sanitized safe_uid)
                    user_result = ldap_client.search_s(
                        'ou=users,' + settings.LDAP_SEARCH_BASE,
                        ldap.SCOPE_SUBTREE,
                        f'(uid={safe_uid})',
                        settings.LDAP_ATTRIBUTES
                    )

                    if not user_result:
                        self.stdout.write(self.style.WARNING(f'User not found for uid: {uid}'))
                        skipped_count += 1
                        continue

                    user_dn, attrs = user_result[0]

                    # Extract user data
                    username = self._get_attr_value(attrs, 'uid')
                    first_name = to_camel_case(self._get_attr_value(attrs, 'givenName'))
                    last_name = to_camel_case(self._get_attr_value(attrs, 'sn'))
                    email = self._get_attr_value(attrs, 'mail')
                    cf = self._get_attr_value(attrs, 'employeeNumber').upper() if self._get_attr_value(attrs, 'employeeNumber') else None

                    if not username:
                        self.stdout.write(self.style.WARNING(f'Skipping user {user_dn} - no uid'))
                        skipped_count += 1
                        continue

                    user_max_group = ""
                    # Determine role from role group memberships
                    for _, gr_attr in groups_result:
                        gr = gr_attr['cn'][0].decode('utf-8') if isinstance(gr_attr['cn'][0], bytes) else gr_attr['cn'][0]
                        if gr in list(settings.LDAP_ROLE_MAPPING.keys()):
                            if user_max_group == "":
                                user_max_group = gr
                            else:
                                if settings.LDAP_ROLE_PRIORITY[settings.LDAP_ROLE_MAPPING[gr]] > settings.LDAP_ROLE_PRIORITY[settings.LDAP_ROLE_MAPPING[user_max_group]]:
                                    user_max_group = gr

                    role = settings.LDAP_ROLE_MAPPING.get(user_max_group, None)

                    if role is None:
                        self.stdout.write(self.style.WARNING(f'Skipping user {username} - no valid role groups'))
                        skipped_count += 1
                        continue

                    processed_usernames.add(username)

                    if dry_run:
                        self.stdout.write(f'Would process: {username} ({first_name} {last_name}) -> role: {role}')
                        continue

                    # Create or update user
                    user, user_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': first_name or '',
                            'last_name': last_name or '',
                            'email': email or '',
                        }
                    )

                    if user_created:
                        self.stdout.write(f'Created user: {username}')
                        created_count += 1
                    elif update_existing:
                        # Check if data has actually changed before updating
                        data_changed = (
                            (first_name and first_name != user.first_name) or
                            (last_name and last_name != user.last_name) or
                            (email and email != user.email)
                        )

                        if data_changed:
                            user.first_name = first_name or user.first_name
                            user.last_name = last_name or user.last_name
                            user.email = email or user.email
                            user.save()
                            self.stdout.write(f'Updated user: {username}')
                            updated_count += 1
                        else:
                            self.stdout.write(f'User {username} already up to date')
                    else:
                        self.stdout.write(f'Skipped existing user: {username}')
                        skipped_count += 1
                        continue

                    # Create or update profile
                    profile, profile_created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'role': role,
                            'is_visible': True,
                            'display_order': 0,
                            'codice_fiscale': cf,
                        }
                    )

                    if not profile_created and update_existing:
                        profile.role = role
                        profile.is_visible = True
                        profile.codice_fiscale = cf
                        profile.save()
                    print(profile.codice_fiscale)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing user {uid}: {e}'))
                    skipped_count += 1
                    continue

            # Remove users that are no longer in LDAP or don't have valid roles
            if not dry_run:
                self._cleanup_obsolete_users(processed_usernames)

            # Cleanup LDAP connection
            ldap_client.unbind()

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f'Dry run completed. Would create {created_count} users.'))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'Completed: {created_count} created, {updated_count} updated, {skipped_count} skipped'
                ))

        except ldap.LDAPError as e:
            self.stdout.write(self.style.ERROR(f'LDAP Error: {e}'))
            return

    def _get_attr_value(self, attrs, attr_name):
        """Get single value from LDAP attribute"""
        values = attrs.get(attr_name, [])
        return values[0].decode('utf-8') if values else None

    def _cleanup_obsolete_users(self, processed_usernames):
        """Remove users that are no longer in LDAP or don't have valid roles"""
        # Find all UserProfile objects where username is not in processed_usernames
        obsolete_profiles = UserProfile.objects.exclude(user__username__in=processed_usernames)
        obsolete_count = obsolete_profiles.count()

        if obsolete_count > 0:
            # Get usernames for logging
            obsolete_usernames = list(obsolete_profiles.values_list('user__username', flat=True))

            # Delete the profiles (this will cascade to users if no other references)
            obsolete_profiles.delete()

            self.stdout.write(f'Removed {obsolete_count} obsolete users: {", ".join(obsolete_usernames[:5])}')
            if obsolete_count > 5:
                self.stdout.write(f'... and {obsolete_count - 5} more')
        else:
            self.stdout.write('No obsolete users to remove')
