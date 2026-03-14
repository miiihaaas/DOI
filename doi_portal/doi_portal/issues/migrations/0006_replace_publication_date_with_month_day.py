"""
Migration: Replace publication_date (DateField) with publication_month and publication_day.

Three-step migration:
1. Add new fields (publication_month, publication_day)
2. Data migration: copy month/day from publication_date
3. Remove old publication_date field
"""

import django.core.validators
from django.db import migrations, models


def copy_date_to_month_day(apps, schema_editor):
    """Copy month and day from publication_date to new fields."""
    Issue = apps.get_model("issues", "Issue")
    for issue in Issue.objects.filter(publication_date__isnull=False):
        issue.publication_month = issue.publication_date.month
        issue.publication_day = issue.publication_date.day
        issue.save(update_fields=["publication_month", "publication_day"])


def reverse_month_day_to_date(apps, schema_editor):
    """Reverse: reconstruct publication_date from month/day/year."""
    import datetime

    Issue = apps.get_model("issues", "Issue")
    for issue in Issue.objects.filter(publication_month__isnull=False):
        try:
            issue.publication_date = datetime.date(
                issue.year,
                issue.publication_month,
                issue.publication_day or 1,
            )
            issue.save(update_fields=["publication_date"])
        except (ValueError, TypeError):
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("issues", "0005_alter_issue_deleted_by"),
    ]

    operations = [
        # Step 1: Add new fields
        migrations.AddField(
            model_name="issue",
            name="publication_month",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(12),
                ],
                verbose_name="Mesec objave",
                help_text="Mesec objave izdanja (opciono)",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="publication_day",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(31),
                ],
                verbose_name="Dan objave",
                help_text="Dan objave izdanja (opciono)",
            ),
        ),
        # Step 2: Data migration
        migrations.RunPython(
            copy_date_to_month_day,
            reverse_month_day_to_date,
        ),
        # Step 3: Remove old field
        migrations.RemoveField(
            model_name="issue",
            name="publication_date",
        ),
    ]
