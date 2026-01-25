# Generated migration for User model extension

from django.db import migrations
from django.db import models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("publishers", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="last_activity",
            field=models.DateTimeField(
                blank=True,
                help_text="Last user activity timestamp",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="publisher",
            field=models.ForeignKey(
                blank=True,
                help_text="Publisher assignment for row-level permissions",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="users",
                to="publishers.publisher",
            ),
        ),
    ]
