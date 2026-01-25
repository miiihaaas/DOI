# Generated migration for Publisher placeholder model

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Publisher",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Publisher name",
                        max_length=255,
                        verbose_name="Name",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated at",
                    ),
                ),
            ],
            options={
                "verbose_name": "Publisher",
                "verbose_name_plural": "Publishers",
            },
        ),
    ]
