from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0008_article_original_language_subtitle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='affiliation',
            name='city',
            field=models.CharField(blank=True, max_length=255, verbose_name='Grad'),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='country',
            field=models.CharField(blank=True, max_length=255, verbose_name='Država'),
        ),
        migrations.CreateModel(
            name='ArticleFunding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('funder_name', models.CharField(max_length=500, verbose_name='Naziv finansijera')),
                ('funder_doi', models.URLField(blank=True, help_text='DOI iz Open Funder Registry (npr. https://doi.org/10.13039/501100004564)', verbose_name='Funder Registry DOI')),
                ('funder_ror_id', models.URLField(blank=True, verbose_name='Funder ROR ID')),
                ('award_number', models.CharField(blank=True, max_length=255, verbose_name='Broj projekta')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Redosled')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fundings', to='articles.article', verbose_name='Članak')),
            ],
            options={
                'verbose_name': 'Finansiranje',
                'verbose_name_plural': 'Finansiranja',
                'ordering': ['order'],
            },
        ),
    ]
