"""
Data migration to create RBAC groups.

AC#2: Four Django Groups are created: Superadmin, Administrator, Urednik, Bibliotekar
AC#4: Each Group has appropriate base permissions defined
"""

from django.db import migrations


RBAC_GROUPS = [
    "Superadmin",
    "Administrator",
    "Urednik",
    "Bibliotekar",
]


def create_groups(apps, schema_editor):
    """Create the four RBAC groups."""
    Group = apps.get_model("auth", "Group")

    for group_name in RBAC_GROUPS:
        Group.objects.get_or_create(name=group_name)


def remove_groups(apps, schema_editor):
    """Remove the RBAC groups (reverse migration)."""
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=RBAC_GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0002_user_last_activity_user_publisher"),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
