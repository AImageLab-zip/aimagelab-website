from django.db import migrations, models
from django.utils.text import slugify


def username_slug(username):
    # Copy of main.models.username_slug, frozen here so later edits to the
    # model do not change what this migration did.
    for char in '.@+':
        username = (username or '').replace(char, '-')
    return (slugify(username) or 'person')[:150]


def slugs_from_username(apps, schema_editor):
    """Replace the name-based slugs of 0016 with username-based ones.

    0016 was never deployed, so no slug has been chosen by hand or linked
    from outside yet; every profile is reset.
    """
    UserProfile = apps.get_model('main', 'UserProfile')
    profiles = list(UserProfile.objects.select_related('user').order_by('pk'))
    # Clear first, so the unique constraint does not trip on a swap.
    UserProfile.objects.update(slug=None)
    used = set()
    for profile in profiles:
        base = username_slug(profile.user.username)
        slug, n = base, 2
        while slug in used:
            slug, n = f'{base}-{n}', n + 1
        used.add(slug)
        profile.slug = slug
        profile.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_author_position_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='slug',
            field=models.SlugField(blank=True, help_text='URL of the personal page: /people/<slug>/. Filled in from the username.', max_length=160, null=True, unique=True),
        ),
        migrations.RunPython(slugs_from_username, migrations.RunPython.noop),
    ]
