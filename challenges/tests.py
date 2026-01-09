from django.test import TestCase
from django.contrib.auth.models import User
from .models import ChallengeTemplate, UserChallenge, DailyCheckin
from django.utils import timezone

class ChallengeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.template = ChallengeTemplate.objects.create(
            title='Test Challenge',
            description='Test Description',
            category='sport',
            duration_days=30,
            difficulty=2
        )
    
    def test_challenge_creation(self):
        self.assertEqual(self.template.title, 'Test Challenge')
        self.assertEqual(self.template.difficulty_stars, '⭐⭐')
    
    def test_user_challenge_progress(self):
        challenge = UserChallenge.objects.create(
            user=self.user,
            template=self.template,
            status='active',
            start_date=timezone.now().date()
        )
        
        DailyCheckin.objects.create(
            user_challenge=challenge,
            date=timezone.now().date(),
            is_completed=True,
            rating=4
        )
        
        self.assertEqual(challenge.completed_days, 1)
        self.assertGreater(challenge.display_progress_percentage, 0)

class ViewTests(TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ChallengeHub')
    
    def test_challenge_list(self):
        response = self.client.get('/challenges/')
        self.assertEqual(response.status_code, 200)