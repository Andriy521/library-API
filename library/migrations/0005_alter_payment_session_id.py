# Generated by Django 5.2.2 on 2025-06-12 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0004_alter_payment_borrowing"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="session_id",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
