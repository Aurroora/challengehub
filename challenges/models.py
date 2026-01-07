from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ChallengeTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('sport', '🏃 Спорт'),
        ('creative', '🎨 Творчество'),
        ('study', '📚 Обучение'),
        ('health', '💊 Здоровье'),
        ('productivity', '⚡ Продуктивность'),
        ('other', '📌 Другое'),
    ]
    
    DIFFICULTY_CHOICES = [
        (1, '⭐ Легко'),
        (2, '⭐⭐ Средне'),
        (3, '⭐⭐⭐ Сложно'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="Категория")
    duration_days = models.IntegerField(verbose_name="Длительность (дней)")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=2, verbose_name="Сложность")
    image = models.ImageField(upload_to='challenge_images/', blank=True, null=True, verbose_name="Изображение")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Шаблон челленджа"
        verbose_name_plural = "Шаблоны челленджей"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def difficulty_stars(self):
        return '⭐' * self.difficulty


class UserChallenge(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('failed', 'Провален'),
        ('paused', 'Приостановлен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    template = models.ForeignKey(ChallengeTemplate, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Шаблон")
    custom_title = models.CharField(max_length=200, blank=True, verbose_name="Название (кастомное)")
    custom_description = models.TextField(blank=True, verbose_name="Описание (кастомное)")
    custom_category = models.CharField(max_length=20, choices=ChallengeTemplate.CATEGORY_CHOICES, blank=True, verbose_name="Категория (кастомная)")
    custom_duration = models.IntegerField(null=True, blank=True, verbose_name="Длительность (кастомная)")
    
    start_date = models.DateField(default=timezone.now, verbose_name="Дата начала")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    current_streak = models.IntegerField(default=0, verbose_name="Текущая серия")
    completed_days = models.IntegerField(default=0, verbose_name="Выполнено дней")
    notes = models.TextField(blank=True, verbose_name="Заметки")
    
    class Meta:
        verbose_name = "Челлендж пользователя"
        verbose_name_plural = "Челленджи пользователей"
        ordering = ['-start_date']
    
    def __str__(self):
        if self.template:
            return f"{self.user.username} - {self.template.title}"
        else:
            return f"{self.user.username} - {self.custom_title}"
    
    @property
    def title(self):
        return self.template.title if self.template else self.custom_title
    
    @property
    def description(self):
        return self.template.description if self.template else self.custom_description
    
    @property
    def category(self):
        return self.template.category if self.template else self.custom_category
    
    @property
    def duration_days(self):
        return self.template.duration_days if self.template else self.custom_duration
    
    @property
    def end_date(self):
        if self.duration_days:
            return self.start_date + timedelta(days=self.duration_days)
        return None
    
    @property
    def days_passed(self):
        return (timezone.now().date() - self.start_date).days + 1
    
    @property
    def days_left(self):
        if self.end_date:
            return max(0, (self.end_date - timezone.now().date()).days)
        return None
    
    @property
    def progress_percentage(self):
        if self.duration_days:
            return min(100, int((self.days_passed / self.duration_days) * 100))
        return 0
    
    @property
    def completion_percentage(self):
        if self.duration_days:
            return int((self.completed_days / self.duration_days) * 100)
        return 0


class DailyCheckin(models.Model):
    RATING_CHOICES = [
        (1, '😞 Плохо'),
        (2, '😐 Нормально'),
        (3, '🙂 Хорошо'),
        (4, '😊 Отлично'),
        (5, '🤩 Супер!'),
    ]
    
    user_challenge = models.ForeignKey(UserChallenge, on_delete=models.CASCADE, related_name='checkins', verbose_name="Челлендж")
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    notes = models.TextField(blank=True, verbose_name="Заметки за день")
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True, verbose_name="Самооценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отметки")
    
    class Meta:
        verbose_name = "Ежедневная отметка"
        verbose_name_plural = "Ежедневные отметки"
        unique_together = ['user_challenge', 'date']
        ordering = ['-date']
    
    def __str__(self):
        status = "✅" if self.is_completed else "❌"
        return f"{self.user_challenge} - {self.date} {status}"