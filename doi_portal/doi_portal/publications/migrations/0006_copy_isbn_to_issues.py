from django.db import migrations


def copy_isbn_to_issues(apps, schema_editor):
    """
    Copy Publication.isbn_print / isbn_online into every child Issue.

    Historically ISBN lived on Publication, which meant every Issue of a
    proceedings series silently shared the same ISBN. This data migration
    lifts the current Publication ISBN down onto each of its Issues so no
    data is lost when the fields are subsequently removed from Publication.
    """
    Publication = apps.get_model("publications", "Publication")

    for publication in Publication.objects.all():
        if not (publication.isbn_print or publication.isbn_online):
            continue
        for issue in publication.issues.all():
            issue.isbn_print = publication.isbn_print
            issue.isbn_online = publication.isbn_online
            issue.save(update_fields=["isbn_print", "isbn_online"])


def noop_reverse(apps, schema_editor):
    """No-op reverse: Issue ISBN fields are cleared by the schema rollback."""


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0005_remove_book_type_edition_series_title"),
        ("issues", "0008_add_isbn_and_external_resource"),
    ]

    operations = [
        migrations.RunPython(copy_isbn_to_issues, noop_reverse),
    ]
