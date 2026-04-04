# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0010_alter_author_options_author_deleted_at_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArticleRelation",
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
                    "relationship_type",
                    models.CharField(
                        choices=[
                            (
                                "Intra-work (isti rad, različite verzije)",
                                [
                                    ("isPreprintOf", "isPreprintOf"),
                                    ("hasPreprint", "hasPreprint"),
                                    ("isManuscriptOf", "isManuscriptOf"),
                                    ("hasManuscript", "hasManuscript"),
                                    ("isExpressionOf", "isExpressionOf"),
                                    ("hasExpression", "hasExpression"),
                                    ("isManifestationOf", "isManifestationOf"),
                                    ("hasManifestation", "hasManifestation"),
                                    ("isReplacedBy", "isReplacedBy"),
                                    ("replaces", "replaces"),
                                    ("isSameAs", "isSameAs"),
                                    ("isIdenticalTo", "isIdenticalTo"),
                                    ("isTranslationOf", "isTranslationOf"),
                                    ("hasTranslation", "hasTranslation"),
                                    ("isVersionOf", "isVersionOf"),
                                    ("hasVersion", "hasVersion"),
                                ],
                            ),
                            (
                                "Inter-work (različiti radovi)",
                                [
                                    ("isSupplementTo", "isSupplementTo"),
                                    ("isSupplementedBy", "isSupplementedBy"),
                                    ("isContinuedBy", "isContinuedBy"),
                                    ("continues", "continues"),
                                    ("isPartOf", "isPartOf"),
                                    ("hasPart", "hasPart"),
                                    ("references", "references"),
                                    ("isReferencedBy", "isReferencedBy"),
                                    ("isBasedOn", "isBasedOn"),
                                    ("isBasisFor", "isBasisFor"),
                                    ("isRequiredBy", "isRequiredBy"),
                                    ("requires", "requires"),
                                    ("isCommentOn", "isCommentOn"),
                                    ("hasComment", "hasComment"),
                                    ("isReplyTo", "isReplyTo"),
                                    ("hasReply", "hasReply"),
                                    ("isReviewOf", "isReviewOf"),
                                    ("hasReview", "hasReview"),
                                ],
                            ),
                        ],
                        max_length=50,
                        verbose_name="Tip relacije",
                    ),
                ),
                (
                    "relation_scope",
                    models.CharField(
                        choices=[
                            ("intra_work", "Intra-work (isti rad)"),
                            ("inter_work", "Inter-work (različiti radovi)"),
                        ],
                        editable=False,
                        max_length=20,
                        verbose_name="Opseg relacije",
                    ),
                ),
                (
                    "identifier_type",
                    models.CharField(
                        choices=[
                            ("doi", "DOI"),
                            ("issn", "ISSN"),
                            ("isbn", "ISBN"),
                            ("uri", "URI"),
                            ("pmid", "PMID"),
                            ("pmcid", "PMCID"),
                            ("arxiv", "arXiv"),
                            ("other", "Ostalo"),
                        ],
                        default="doi",
                        max_length=10,
                        verbose_name="Tip identifikatora",
                    ),
                ),
                (
                    "target_identifier",
                    models.CharField(
                        max_length=500,
                        verbose_name="Identifikator cilja",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Opis",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "article",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="relations",
                        to="articles.article",
                        verbose_name="Članak",
                    ),
                ),
            ],
            options={
                "verbose_name": "Relacija članka",
                "verbose_name_plural": "Relacije članaka",
                "ordering": ["order"],
            },
        ),
    ]
