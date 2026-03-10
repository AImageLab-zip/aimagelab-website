from django.core.management.base import BaseCommand
from main.models import DashboardCard


CARDS = [
    {
        'title': 'UNIMORE Missioni',
        'description': 'Applications to compile documents for mission reimbursements.',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://github.com/prittt/missioni-unimore/raw/master/RimborsiApp/static/RimborsiApp/imgs/missioni_logo.png',
        'link_type': 'external',
        'link_url': 'https://missioni.ing.unimore.it/',
        'display_order': 0,
    },
    {
        'title': 'Richieste DIEF',
        'description': 'Digital platform for automated management of requests and approval processes.',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://richieste.ing.unimore.it/static/images/logo.png',
        'link_type': 'external',
        'link_url': 'https://richieste.ing.unimore.it/',
        'display_order': 1,
    },
    {
        'title': 'AILB SRV Coldfront',
        'description': 'Access to AImageLab services via Coldfront.',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://ailb-web.ing.unimore.it//coldfront/static/common/images/apple-touch-icon.png',
        'link_type': 'external',
        'link_url': 'https://ailb-web.ing.unimore.it/coldfront',
        'display_order': 2,
    },
    {
        'title': 'AILB Tickets',
        'description': 'Ticketing system for inquiries related to our cluster.',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://ailb-web.ing.unimore.it//coldfront/static/common/images/apple-touch-icon.png',
        'link_type': 'external',
        'link_url': 'https://ailb-web.ing.unimore.it/tickets/',
        'display_order': 3,
    },
    {
        'title': 'DIEF Intranet',
        'description': 'Quick access to the DIEF intranet.',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://web.ing.unimo.it/wiki/skins/dief/sigillo_small.png?118bf',
        'link_type': 'external',
        'link_url': 'https://web.ing.unimo.it/wiki/index.php/Intranet_DIEF',
        'display_order': 4,
    },
    {
        'title': 'Meeting Room Booking',
        'description': 'Book meeting rooms at DIEF',
        'section': 'At a Glance',
        'logo_type': 'external',
        'logo_external_url': 'https://web.ing.unimo.it/wiki/skins/dief/sigillo_small.png?118bf',
        'link_type': 'external',
        'link_url': 'https://web.ing.unimo.it/wiki/index.php/Intranet_DIEF#Prenotazione_sale_riunioni',
        'display_order': 5,
    },
    {
        'title': 'Small Expense Reimbursement',
        'description': 'Forms for small expense reimbursements.',
        'section': 'At a Glance',
        'logo_type': 'lucide',
        'logo_lucide_icon': 'coins',
        'link_type': 'external',
        'link_url': 'https://web.ing.unimo.it/DocumentiPubblici/dief/altre-attivita/rimborso%20piccole%20spese/',
        'display_order': 6,
    },
]


class Command(BaseCommand):
    help = 'Populate dashboard cards with default data'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for card_data in CARDS:
            _, was_created = DashboardCard.objects.get_or_create(
                title=card_data['title'],
                section=card_data['section'],
                defaults=card_data,
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {card_data['title']}"))
            else:
                skipped += 1
                self.stdout.write(f"  Skipped (already exists): {card_data['title']}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created}, skipped {skipped}."
        ))
