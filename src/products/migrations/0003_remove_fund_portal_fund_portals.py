# Generated by Django 4.1.4 on 2022-12-12 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("products", "0002_rename_management_company_fund_company"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fund",
            name="portal",
        ),
        migrations.AddField(
            model_name="fund",
            name="portals",
            field=models.ManyToManyField(to="sites.site"),
        ),
    ]
