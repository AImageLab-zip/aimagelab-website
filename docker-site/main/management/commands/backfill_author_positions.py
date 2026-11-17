from collections import Counter

from django.core.management.base import BaseCommand

from main import authorship
from main.models import UserProfilePublicationIRIS


class Command(BaseCommand):
    help = (
        "Work out each lab member's position in the author list of their "
        "publications (issue #13) and report how many could be resolved. "
        "Needs no IRIS traffic: it reads the stored author strings."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report only, write nothing')
        parser.add_argument('--show', type=int, default=15,
                            help='How many unresolved links to list (default 15)')

    def handle(self, *args, **options):
        links = UserProfilePublicationIRIS.objects.select_related(
            'user_profile__user', 'publication')
        counts, unresolved, truncated, changed = Counter(), [], 0, 0

        for link in links.iterator():
            before = (link.posizione, link.n_authors, link.position_status)
            link.compute_position()
            counts[link.position_status] += 1
            if link.n_authors == 0:
                truncated += 1
            if link.position_status not in authorship.RESOLVED:
                unresolved.append(link)
            if before != (link.posizione, link.n_authors, link.position_status):
                changed += 1
                if not options['dry_run']:
                    link.save(update_fields=['posizione', 'n_authors', 'position_status'])

        total = sum(counts.values())
        self.stdout.write(f'{total} author links')
        for status, label in authorship.STATUS_CHOICES:
            if counts[status]:
                share = 100 * counts[status] / total
                self.stdout.write(f'  {label:<34} {counts[status]:>6}  {share:5.1f}%')
        self.stdout.write(
            f'  author list truncated (last position unknown): {truncated}')

        if unresolved and options['show']:
            self.stdout.write('\nUnresolved (first %d):' % options['show'])
            for link in unresolved[:options['show']]:
                user = link.user_profile.user
                self.stdout.write(
                    f'  [{link.position_status}] {user.first_name} {user.last_name}'
                    f' in: {(link.publication.autori or "")[:110]}')

        verb = 'would change' if options['dry_run'] else 'updated'
        self.stdout.write(self.style.SUCCESS(f'{verb} {changed} link(s)'))
