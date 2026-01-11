from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='timezone',
            field=models.CharField(default='UTC', max_length=64, verbose_name='Time Zone'),
        ),
    ]
