# Generated by Django 4.2.4 on 2024-11-06 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_remove_drug_unique_draft_per_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='illness',
            name='spread',
            field=models.TextField(),
        ),
    ]
