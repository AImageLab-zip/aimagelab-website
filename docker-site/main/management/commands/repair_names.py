from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from main.text_utils import repair_mojibake


class Command(BaseCommand):
    help = (
        "Repair first/last names stored with broken accents "
        "('Niccolã²' -> 'Niccolò', issue #28). Shows the changes; "
        "pass --apply to write them."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Write the repaired names (default: only list them)',
        )

    def handle(self, *args, **options):
        changed = 0
        for user in User.objects.all().iterator():
            first = repair_mojibake(user.first_name)
            last = repair_mojibake(user.last_name)
            if first == user.first_name and last == user.last_name:
                continue
            changed += 1
            self.stdout.write(
                f'{user.username}: {user.first_name!r} {user.last_name!r}'
                f' -> {first!r} {last!r}'
            )
            if options['apply']:
                user.first_name, user.last_name = first, last
                user.save(update_fields=['first_name', 'last_name'])

        verb = 'Repaired' if options['apply'] else 'Would repair'
        self.stdout.write(self.style.SUCCESS(f'{verb} {changed} user(s).'))
        if changed and not options['apply']:
            self.stdout.write('Run again with --apply to write the changes.')
