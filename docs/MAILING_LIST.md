# Mailing List

The AImageLab mailing list allows authorised senders to broadcast messages to lab members and external recipients.  
Incoming emails are checked against a list of trusted senders, routed to the right audience via **plus-addressing**, and either delivered automatically or held for moderator review.

---

## Sending an email

Send a message to one of the plus-addressed list addresses below.
The suffix after the `+` determines who receives the message:

| Address | Recipients |
|---|---|
| `aimagelab+all@unimore.it` | All active members + external recipients |
| `aimagelab+active@unimore.it` | All active members (no externals) |
| `aimagelab+esterni@unimore.it` | External recipients only |
| `aimagelab+strutturati@unimore.it` | Rector, professors, RTT/RTD-A/RTD-B researchers |
| `aimagelab+docenti@unimore.it` | Rector, full professors, associate professors |
| `aimagelab+dottorandi@unimore.it` | PhD students |
| `aimagelab+postdocs@unimore.it` | Postdoctoral researchers |
| `aimagelab+staff@unimore.it` | Secretariat and administrative staff |

**Examples:**

```
To: aimagelab+all@unimore.it
Subject: Department seminar on Friday

To: aimagelab+dottorandi@unimore.it
Subject: PhD course — schedule update

To: aimagelab+strutturati@unimore.it, aimagelab+staff@unimore.it
Subject: Faculty board reminder
```

To send to multiple groups, add multiple recipients in the To or Cc field.
The final recipient list is the **union** of all matched groups.

If the email is sent to `aimagelab@unimore.it` (without a `+suffix`), the message is delivered to all active members (equivalent to `aimagelab+active@unimore.it`).

### Replying

Every forwarded email includes the list address(es) in Cc:

- **Reply** — goes to the original sender only.
- **Reply All** — goes to the original sender **and** back to the list (e.g. `aimagelab+strutturati@unimore.it`), so the reply is redistributed to the same group.

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

Routing rules (plus-address suffixes → role lists) are managed from the Django admin:

```
/admin/mailinglist/subjectroleroute/
```

Each rule defines:
- **Tag** — the plus-address suffix (e.g. `staff` for `aimagelab+staff@unimore.it`)
- **Roles** — list of user roles that receive messages sent to this address
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
