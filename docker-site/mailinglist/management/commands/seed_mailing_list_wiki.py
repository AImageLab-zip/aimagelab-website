"""
Create or update the Mailing List wiki page.

Usage:
    python manage.py seed_mailing_list_wiki
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

WIKI_SLUG = 'mailing-list'
WIKI_TITLE = 'Mailing List'

WIKI_CONTENT = """\
The AImageLab mailing list allows authorised senders to broadcast messages to lab members and \
external recipients. Incoming emails are routed to the right audience via **plus-addressing** \
and either delivered automatically (trusted senders) or held for moderator review.

---

## Sending an email

Place a tagged address in the **To** or **Cc** field of your email client to target the \
desired group:

```
aimagelab+<tag>@unimore.it
```

The subject line is forwarded unchanged — no tags are visible to recipients.

You can target multiple groups simultaneously by adding several addresses to the To/Cc field. \
The final recipient list is the **union** of all matched groups.

If you use the plain address `aimagelab@unimore.it` with no suffix, the message is delivered \
to all current active lab members (equivalent to `+default`).

---

## Routing tags

| Recipient address | Description | |
|---|---|---|
| `aimagelab+default@unimore.it` | All current active members (no past members, no externals) | <button class="btn btn-ghost btn-xs" data-ml-tag="default">View recipients</button> |
| `aimagelab+all@unimore.it` | All active + past members + external recipients | <button class="btn btn-ghost btn-xs" data-ml-tag="all">View recipients</button> |
| `aimagelab+past@unimore.it` | Past lab members only | <button class="btn btn-ghost btn-xs" data-ml-tag="past">View recipients</button> |
| `aimagelab+esterni@unimore.it` | External recipients only | <button class="btn btn-ghost btn-xs" data-ml-tag="esterni">View recipients</button> |
| `aimagelab+strutturati@unimore.it` | Rector, professors, RTT/RTD-A/RTD-B researchers | <button class="btn btn-ghost btn-xs" data-ml-tag="strutturati">View recipients</button> |
| `aimagelab+proff@unimore.it` | Rector, full and associate professors | <button class="btn btn-ghost btn-xs" data-ml-tag="proff">View recipients</button> |
| `aimagelab+non-strutturati@unimore.it` | Research fellows, collaborators, interns, PhD students | <button class="btn btn-ghost btn-xs" data-ml-tag="non-strutturati">View recipients</button> |
| `aimagelab+dottorandi@unimore.it` | PhD students | <button class="btn btn-ghost btn-xs" data-ml-tag="dottorandi">View recipients</button> |
| `aimagelab+staff@unimore.it` | Secretariat and administrative staff | <button class="btn btn-ghost btn-xs" data-ml-tag="staff">View recipients</button> |

The **View recipients** button shows the current live list of addresses that would receive a \
message for that tag.

**Examples:**

```
To: aimagelab+dottorandi@unimore.it
Subject: PhD course — schedule update
```

```
To: aimagelab+strutturati@unimore.it, aimagelab+staff@unimore.it
Subject: Faculty board reminder
```

---

## Moderation

### Trusted senders (auto-approved)

Emails from addresses in trusted domains (e.g. `@unimore.it`) are forwarded automatically \
without moderator review.

### Untrusted senders (pending moderation)

Emails from other domains are held in the moderation queue. A staff moderator must approve \
or reject each message before it is forwarded. Moderators are notified by email when a new \
message requires attention.

The moderation interface is at `/mailinglist/moderation/` *(staff only)*.

| Action | Effect |
|---|---|
| **Approve** | Forwards the message to the resolved recipient list |
| **Reject** | Discards the message without forwarding |
| **Reject & Blacklist Sender** | Discards the message and blocks all future emails from that address |
| **Approve & Whitelist Sender** | Approves and forwards; all future emails from that address are auto-approved |

When a sender is blacklisted, any other pending messages from the same address are \
automatically rejected at the same time.

---

## Managing your subscription

Every forwarded message includes an **Unsubscribe** link in the footer. Clicking it immediately \
removes that address (primary or extra) from all future deliveries, without requiring a login.

To re-subscribe or manage additional delivery addresses, log in and visit your profile preferences.

---

## For administrators

> All `manage.py` commands below must be run inside the Django container.
> From the repository root:
>
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.prod.yml exec django-app python manage.py <command>
> ```

### Routing rules

Routing tags (suffix → role list) are managed from the Django admin at \
`/admin/mailinglist/subjectroleroute/`.

Each rule defines:

- **Tag** — the plus-address suffix (e.g. `strutturati` → `aimagelab+strutturati@unimore.it`)
- **Roles** — list of user-profile role keys that receive messages with this tag; \
use `__admin__` to target Django staff users
- **Send to external** — whether external (non-system) recipients are included

To seed or reset the routes to their default values:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec django-app python manage.py seed_mailinglist_routes
```

> **Note:** running the seed command also removes obsolete tags (`active`, `docenti`, `postdocs`) \
> if they are still present in the database.

The `admin` tag (`aimagelab+admin@unimore.it`) is intentionally excluded from the table above \
as it targets only Django staff users and is not intended for general use.

### Blacklist / Whitelist

Blocked and trusted senders can be managed from the Django admin:

- `/admin/mailinglist/blacklistedsender/`
- `/admin/mailinglist/whitelistedsender/`

They can also be set directly from the moderation detail page via the \
**Reject & Blacklist** / **Approve & Whitelist** actions.

### External recipients

People who are not system users but should receive list mail can be added at \
`/admin/mailinglist/externalrecipient/`.

### Email polling

Incoming mail is fetched from Gmail IMAP every **3 minutes** via Celery Beat. \
To trigger a fetch immediately:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec django-app python manage.py fetch_emails
```
"""


class Command(BaseCommand):
    help = 'Create or update the Mailing List wiki page'

    def handle(self, *args, **options):
        from main.models import WikiPage

        # Use the first superuser as the author, falling back to any staff user
        author = (
            User.objects.filter(is_superuser=True, is_active=True).first()
            or User.objects.filter(is_staff=True, is_active=True).first()
        )
        if not author:
            self.stderr.write('No staff or superuser found — cannot set page author.')
            return

        page, created = WikiPage.objects.update_or_create(
            slug=WIKI_SLUG,
            defaults={
                'title': WIKI_TITLE,
                'content': WIKI_CONTENT,
                'is_published': True,
                'updated_by': author,
            },
        )

        if created:
            page.created_by = author
            page.save(update_fields=['created_by'])
            self.stdout.write(self.style.SUCCESS(f'Created wiki page "{WIKI_TITLE}" (/{WIKI_SLUG}/)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated wiki page "{WIKI_TITLE}" (/{WIKI_SLUG}/)'))
