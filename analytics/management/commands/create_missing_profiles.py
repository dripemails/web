from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analytics.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile instances for users who don\'t have them'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        count = 0
        
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for user: {user.username}')
            )
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have profiles!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created {count} user profiles')
            )
