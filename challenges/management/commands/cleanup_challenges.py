from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from challenges.models import UserChallenge

class Command(BaseCommand):
    help = 'Удаляет завершенные челленджи старше 30 дней'

    def handle(self, *args, **kwargs):
        threshold = timezone.now().date() - timedelta(days=30)
        old_challenges = UserChallenge.objects.filter(
            status__in=['completed', 'failed'],
            start_date__lt=threshold
        )
        
        count = old_challenges.count()
        old_challenges.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Удалено {count} старых челленджей'))