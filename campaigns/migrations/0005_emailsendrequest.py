from django.db import migrations, models
import uuid
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscribers', '0001_initial'),
        ('campaigns', '0004_alter_email_wait_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSendRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subscriber_email', models.EmailField(max_length=254, verbose_name='Subscriber Email')),
                ('variables', models.JSONField(blank=True, default=dict, verbose_name='Variables')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('queued', 'Queued'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=10, verbose_name='Status')),
                ('scheduled_for', models.DateTimeField(verbose_name='Scheduled For')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Sent At')),
                ('error_message', models.TextField(blank=True, verbose_name='Error Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_send_requests', to='campaigns.campaign', verbose_name='Campaign')),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='send_requests', to='campaigns.email', verbose_name='Email')),
                ('subscriber', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='send_requests', to='subscribers.subscriber', verbose_name='Subscriber')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_send_requests', to='auth.user', verbose_name='User')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Email Send Request',
                'verbose_name_plural': 'Email Send Requests',
            },
        ),
    ]
