"""
Recover conference venues from citations already stored in the database.

No IRIS calls: every affected row already has the citation text, the venue
was simply never parsed out of it.
"""
from django.core.management.base import BaseCommand

from main.models import PublicationIRIS
from main.venue_parser import extract_venue, short_name


class Command(BaseCommand):
    help = 'Backfill conferenza/conferenza_nome from stored citations'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--all', action='store_true',
                            help='Reparse every proceedings row, not just empty ones')

    def handle(self, *args, **options):
        qs = PublicationIRIS.objects.filter(tipo__icontains='Convegno')
        if not options['all']:
            qs = qs.filter(conferenza='')
        total = qs.count()
        done = skipped = 0
        for pub in qs.iterator():
            venue = extract_venue(pub.citation)
            if not venue:
                skipped += 1
                continue
            if options['dry_run']:
                done += 1
                continue
            pub.conferenza = venue[:500]
            pub.conferenza_nome = short_name(venue)[:200]
            fields = ['conferenza', 'conferenza_nome']
            if not pub.rivista:
                pub.rivista = (pub.conferenza_nome or venue)[:500]
                fields.append('rivista')
            pub.save(update_fields=fields)
            done += 1
        verb = 'would update' if options['dry_run'] else 'updated'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} {done} of {total} proceedings ({skipped} had no parsable venue)'))
