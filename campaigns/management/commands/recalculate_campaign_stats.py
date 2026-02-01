"""
Management command to recalculate campaign statistics from EmailEvent data.
This ensures all campaign metrics are accurate and up to date.
"""
from django.core.management.base import BaseCommand
from campaigns.models import Campaign, EmailEvent
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Recalculate all campaign statistics from EmailEvent data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=str,
            help='Recalculate stats for a specific campaign ID',
        )

    def handle(self, *args, **options):
        campaign_id = options.get('campaign_id')
        
        if campaign_id:
            campaigns = Campaign.objects.filter(id=campaign_id)
            if not campaigns.exists():
                self.stdout.write(self.style.ERROR(f'Campaign with ID {campaign_id} not found'))
                return
        else:
            campaigns = Campaign.objects.all()
        
        total_campaigns = campaigns.count()
        self.stdout.write(f'Recalculating statistics for {total_campaigns} campaign(s)...')
        
        for campaign in campaigns:
            # Get all events for this campaign's emails
            events = EmailEvent.objects.filter(email__campaign=campaign)
            
            # Count each event type
            sent_count = events.filter(event_type='sent').count()
            open_count = events.filter(event_type='opened').count()
            click_count = events.filter(event_type='clicked').count()
            bounce_count = events.filter(event_type='bounced').count()
            unsubscribe_count = events.filter(event_type='unsubscribed').count()
            complaint_count = events.filter(event_type='complained').count()
            
            # Update campaign
            campaign.sent_count = sent_count
            campaign.open_count = open_count
            campaign.click_count = click_count
            campaign.bounce_count = bounce_count
            campaign.unsubscribe_count = unsubscribe_count
            campaign.complaint_count = complaint_count
            campaign.save(update_fields=[
                'sent_count', 'open_count', 'click_count', 
                'bounce_count', 'unsubscribe_count', 'complaint_count'
            ])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Campaign "{campaign.name}": '
                    f'sent={sent_count}, opened={open_count}, clicked={click_count}, '
                    f'bounced={bounce_count}, unsubscribed={unsubscribe_count}, complained={complaint_count}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully recalculated statistics for {total_campaigns} campaign(s)'))
