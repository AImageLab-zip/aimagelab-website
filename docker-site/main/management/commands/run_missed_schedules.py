"""
Re-dispatch daily Celery beat tasks whose window was missed while the host
was down.

Celery beat has no equivalent of systemd's Persistent=true: if the machine is
off at the scheduled minute, that run is simply skipped and nothing records
it. On 2026-10-19 the host was down 01:45-09:10, so both the 02:00 LDAP sync
and the 03:00 photo import vanished, and people who had gained an
employeeNumber that day stayed without a codice_fiscale - and so without a
profile photo - until someone noticed.

This runs from entrypoint.sh on container start. It deliberately does NOT
re-run a task that already ran on schedule; otherwise an ordinary deploy
(which restarts django-app) would fire a full LDAP sync and photo import
every time.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


# Task name -> how stale its last run must be before we consider it missed.
# A daily task is overdue once more than ~a day has passed, with a little
# slack so a run that merely started late is not re-fired.
CATCHUP_AFTER = {
    'Daily LDAP User Sync': timedelta(hours=25),
    'Daily IRIS Profile Photos Import': timedelta(hours=25),
}


class Command(BaseCommand):
    help = 'Re-dispatch daily periodic tasks missed while the host was down'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be dispatched, change nothing')

    def handle(self, *args, **options):
        # Never let a catch-up problem stop the container from starting.
        try:
            from django_celery_beat.models import PeriodicTask
            from myproject.celery import app as celery_app
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.WARNING(
                f'catch-up skipped (imports unavailable): {exc}'))
            return

        now = timezone.now()
        for name, max_age in CATCHUP_AFTER.items():
            try:
                task = PeriodicTask.objects.filter(name=name).first()
                if task is None:
                    self.stdout.write(f'  {name}: not registered yet, nothing to catch up')
                    continue
                if not task.enabled:
                    self.stdout.write(f'  {name}: disabled, skipping')
                    continue

                last = task.last_run_at
                if last is not None and (now - last) <= max_age:
                    age = now - last
                    self.stdout.write(
                        f'  {name}: ran {int(age.total_seconds() // 3600)}h ago, up to date')
                    continue

                reason = 'never run' if last is None else f'last run {last:%Y-%m-%d %H:%M %Z}'
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING(
                        f'  {name}: WOULD dispatch ({reason})'))
                    continue

                # Queue it rather than running inline: entrypoint must not
                # block container startup for the length of the task. Redis is
                # already healthy at this point (django-app depends on it), so
                # a worker picks this up as soon as one is ready.
                celery_app.send_task(task.task)

                # Record the dispatch. send_task() does not touch last_run_at -
                # only beat does - so without this the staleness check above
                # would still see the old timestamp and re-dispatch on every
                # single container restart, which is what the check exists to
                # prevent. Beat computes the next due time from last_run_at, so
                # stamping it now simply moves the next run to tomorrow's slot.
                task.last_run_at = now
                task.save(update_fields=['last_run_at'])

                self.stdout.write(self.style.SUCCESS(
                    f'  {name}: dispatched catch-up run ({reason})'))
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(
                    f'  {name}: catch-up failed, continuing anyway: {exc}'))
