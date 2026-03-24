# Mailing List

The AImageLab mailing list allows authorised senders to broadcast messages to lab members and external recipients.  
Incoming emails are checked against a list of trusted senders, routed to the right audience via **subject tags**, and either delivered automatically or held for moderator review.

---

## Sending an email

Send a message to the list address:

```
anonymous.user.conferences@gmail.com
```

Include one or more **routing tags** at the start of the subject line to control who receives the message:

| Tag | Recipients |
|---|---|
| `@ailb-all` | All active members + external recipients |
| `@ailb-active` | All active members (no externals) |
| `@ailb-esterni` | External recipients only |
| `@ailb-strutturati` | Rector, professors, RTT/RTD-A/RTD-B researchers |
| `@ailb-docenti` | Rector, full professors, associate professors |
| `@ailb-dottorandi` | PhD students |
| `@ailb-postdocs` | Postdoctoral researchers |
| `@ailb-staff` | Secretariat and administrative staff |

**Examples:**

```
Subject: @ailb-all Department seminar on Friday
Subject: @ailb-dottorandi PhD course — schedule update
Subject: @ailb-strutturati @ailb-staff Faculty board reminder
```

Multiple tags are supported. The final recipient list is the **union** of all matched groups.  
Tags are stripped from the subject before the message is forwarded, so recipients only see the clean subject.

If **no tag** is specified, the message is delivered to all active members (equivalent to `@ailb-active`).

---

## Moderation

### Trusted senders (auto-approved)

Emails from addresses with a trusted domain (e.g. `@unimore.it`) are forwarded automatically without requiring moderator approval.

### Untrusted senders (pending moderation)

Emails from other domains are held in the moderation queue. A moderator must review and approve or reject each message before it is forwarded.

Moderators can act from the moderation interface at:

```
/mailinglist/moderation/
```

Available actions per message:

| Action | Effect |
|---|---|
| **Approve** | Forwards the message to the resolved recipient list |
| **Reject** | Discards the message without forwarding |
| **Reject & Blacklist Sender** | Discards the message and blocks all future emails from that address |
| **Approve & Whitelist Sender** | Approves and forwards; all future emails from that address are auto-approved |

When a sender is blacklisted, any other pending messages from the same address are automatically rejected at the same time.

---

## Managing your subscription

Each recipient can manage their own subscription via the unsubscribe link included in every forwarded message.  
Clicking the link immediately unsubscribes that specific address (primary email or extra address) without requiring a login.

To re-subscribe or manage extra email addresses, log in and visit your profile preferences.

---

## For administrators

> **Note:** all `manage.py` commands below must be run **inside the Django container**, not directly on the host.  
> From the repository root:
> ```bash
> docker compose exec django-app python manage.py <command>
> ```

### Routing rules

Routing rules (tags → role lists) are managed from the Django admin:

```
/admin/mailinglist/subjectroleroute/
```

Each rule defines:
- **Tag** — the `@ailb-*` string to match in the subject
- **Roles** — list of user roles that receive messages with this tag
- **Send to external** — whether external (non-system) recipients are included

To seed the default production routes:

```bash
docker compose exec django-app python manage.py seed_mailinglist_routes
```

### Blacklist / Whitelist

Blocked and trusted senders are managed from the Django admin:

```
/admin/mailinglist/blacklistedsender/
/admin/mailinglist/whitelistedsender/
```

### External recipients

People who are not system users but should receive list mail can be added at:

```
/admin/mailinglist/externalrecipient/
```

### Email polling

Incoming mail is fetched from Gmail IMAP every **3 minutes** via Celery Beat.  
To trigger a fetch immediately:

```bash
docker compose exec django-app python manage.py fetch_emails
```
