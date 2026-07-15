from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0006_copy_isbn_to_issues"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="publication",
            name="isbn_print",
        ),
        migrations.RemoveField(
            model_name="publication",
            name="isbn_online",
        ),
    ]
