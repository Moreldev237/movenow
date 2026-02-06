# Generated migration for referral_code field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='referral_code',
            field=models.CharField(
                blank=True,
                help_text="Code de parrainage",
                max_length=20,
                null=True,
                unique=True,
            ),
        ),
    ]

