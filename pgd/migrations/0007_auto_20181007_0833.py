# Generated by Django 2.0.8 on 2018-10-07 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pgd', '0006_galleryimage_content_page'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blogpage',
            options={'verbose_name': 'Article category', 'verbose_name_plural': 'Article categories'},
        ),
        migrations.AlterModelOptions(
            name='postpage',
            options={'verbose_name': 'article', 'verbose_name_plural': 'articles'},
        ),
    ]
