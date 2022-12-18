# Generated by Django 4.1.4 on 2022-12-18 19:47

from django.db import migrations, models
import django_jsonform.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('crm', '0009_alter_company_extra_alter_contact_extra'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='extra',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='company',
            name='portals',
            field=models.ManyToManyField(blank=True, to='sites.site'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='extra',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='contact',
            name='portals',
            field=models.ManyToManyField(blank=True, to='sites.site'),
        ),
        migrations.AlterField(
            model_name='extrafieldschema',
            name='schema',
            field=django_jsonform.models.fields.JSONField(),
        ),
    ]