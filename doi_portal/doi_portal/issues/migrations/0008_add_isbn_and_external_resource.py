from django.db import migrations, models

import doi_portal.publications.validators


class Migration(migrations.Migration):

    dependencies = [
        ("issues", "0007_add_doi_suffix_pdf_to_issue"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="isbn_print",
            field=models.CharField(
                blank=True,
                help_text="Format: 978-X-XXXX-XXXX-X",
                max_length=17,
                validators=[doi_portal.publications.validators.validate_isbn],
                verbose_name="ISBN (štampano)",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="isbn_online",
            field=models.CharField(
                blank=True,
                max_length=17,
                validators=[doi_portal.publications.validators.validate_isbn],
                verbose_name="ISBN (online)",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="use_external_resource",
            field=models.BooleanField(
                default=False,
                help_text="Ako je uključeno, DOI za izdanje će pokazivati na sajt izdavača umesto na portal.",
                verbose_name="Koristi eksterni URL za DOI",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="external_landing_url",
            field=models.URLField(
                blank=True,
                help_text="URL stranice zbornika na sajtu izdavača",
                max_length=500,
                verbose_name="Eksterna landing stranica",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="external_pdf_url",
            field=models.URLField(
                blank=True,
                help_text="URL PDF fajla zbornika na sajtu izdavača (opciono)",
                max_length=500,
                verbose_name="Eksterni PDF URL",
            ),
        ),
    ]
