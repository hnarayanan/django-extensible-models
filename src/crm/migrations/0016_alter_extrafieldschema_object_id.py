# Generated by Django 4.1.4 on 2022-12-18 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0015_alter_company_portals_alter_contact_portals_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="extrafieldschema",
            name="object_id",
            field=models.UUIDField(null=True),
        ),
    ]