# Generated migration for Publisher model extension (Story 2.1)

import doi_portal.publishers.models
from django.conf import settings
from django.db import migrations
from django.db import models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("publishers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update name field verbose_name to Serbian
        migrations.AlterField(
            model_name="publisher",
            name="name",
            field=models.CharField(
                help_text="Naziv izdavaca",
                max_length=255,
                verbose_name="Naziv",
            ),
        ),
        # Add slug field
        migrations.AddField(
            model_name="publisher",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="URL-friendly verzija naziva",
                max_length=255,
                unique=True,
                verbose_name="Slug",
                default="",  # Temporary default
            ),
            preserve_default=False,
        ),
        # Add description field
        migrations.AddField(
            model_name="publisher",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Opis izdavaca",
                verbose_name="Opis",
            ),
        ),
        # Add logo field
        migrations.AddField(
            model_name="publisher",
            name="logo",
            field=models.ImageField(
                blank=True,
                help_text="Logo izdavaca (JPG, PNG, SVG, max 2MB)",
                null=True,
                upload_to="publishers/logos/",
                verbose_name="Logo",
            ),
        ),
        # Add contact_email field
        migrations.AddField(
            model_name="publisher",
            name="contact_email",
            field=models.EmailField(
                blank=True,
                help_text="Email adresa za kontakt",
                max_length=254,
                verbose_name="Kontakt email",
            ),
        ),
        # Add contact_phone field
        migrations.AddField(
            model_name="publisher",
            name="contact_phone",
            field=models.CharField(
                blank=True,
                help_text="Broj telefona za kontakt",
                max_length=50,
                verbose_name="Kontakt telefon",
            ),
        ),
        # Add website field
        migrations.AddField(
            model_name="publisher",
            name="website",
            field=models.URLField(
                blank=True,
                help_text="URL web sajta izdavaca",
                verbose_name="Web sajt",
            ),
        ),
        # Add doi_prefix field (required, unique, with validator)
        migrations.AddField(
            model_name="publisher",
            name="doi_prefix",
            field=models.CharField(
                help_text="DOI prefiks u formatu '10.XXXX' (npr. '10.1234')",
                max_length=20,
                unique=True,
                validators=[doi_portal.publishers.models.validate_doi_prefix],
                verbose_name="DOI prefiks",
                default="10.0000",  # Temporary default for existing rows
            ),
            preserve_default=False,
        ),
        # Add soft delete fields
        migrations.AddField(
            model_name="publisher",
            name="is_deleted",
            field=models.BooleanField(
                default=False,
                verbose_name="Obrisano",
            ),
        ),
        migrations.AddField(
            model_name="publisher",
            name="deleted_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Vreme brisanja",
            ),
        ),
        migrations.AddField(
            model_name="publisher",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="deleted_publishers",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Obrisao",
            ),
        ),
        # Update timestamps verbose_name to Serbian
        migrations.AlterField(
            model_name="publisher",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name="Kreirano",
            ),
        ),
        migrations.AlterField(
            model_name="publisher",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                verbose_name="Azurirano",
            ),
        ),
        # Update model options
        migrations.AlterModelOptions(
            name="publisher",
            options={
                "ordering": ["name"],
                "verbose_name": "Izdavac",
                "verbose_name_plural": "Izdavaci",
            },
        ),
    ]
