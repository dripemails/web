from django.test import TestCase, Client
from django.contrib.auth.models import User
from campaigns.models import Campaign, Email, EmailEvent


class SendEmailAnalyticsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='pass')
        self.client = Client()
        self.client.force_login(self.user)

        self.campaign = Campaign.objects.create(user=self.user, name='Test Campaign')
        self.email = Email.objects.create(campaign=self.campaign, subject='Hello', body_html='<p>hi</p>', body_text='hi')

    def test_send_api_creates_email_event_and_updates_campaign(self):
        url = f'/api/campaigns/{self.campaign.id}/emails/{self.email.id}/send/'
        before_events = EmailEvent.objects.filter(email=self.email, event_type='sent').count()
        response = self.client.post(url, data={'email': 'verify@test.invalid', 'send_immediately': True}, content_type='application/json')
        self.assertEqual(response.status_code, 200, msg=response.content)

        after_events = EmailEvent.objects.filter(email=self.email, event_type='sent').count()
        self.assertGreater(after_events, before_events, 'Expected a sent EmailEvent to be created')

        # campaign.sent_count should be incremented by the EmailEvent post_save signal
        self.campaign.refresh_from_db()
        self.assertGreaterEqual(self.campaign.sent_count, 1)
