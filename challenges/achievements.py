# achievements.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from .models import Achievement, UserChallenge, DailyCheckin

def check_and_create_achievements(user):
    """Проверяет и создает достижения для пользователя"""
    
    achievements_created = []
    
    # 1. Проверяем достижение "Первая отметка"
    first_checkin = DailyCheckin.objects.filter(
        user_challenge__user=user
    ).order_by('date').first()
    
    if first_checkin:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='streak',
            title='Первый шаг',
            defaults={
                'description': 'Сделал первую отметку в челлендже',
                'icon': '👣',
                'progress': 1,
                'target': 1
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 2. Проверяем достижение "Неделя подряд"
    today = timezone.now().date()
    
    # Считаем, сколько дней подряд пользователь отмечался
    consecutive_days = 0
    current_date = today
    
    while True:
        has_checkin = DailyCheckin.objects.filter(
            user_challenge__user=user,
            date=current_date,
            is_completed=True
        ).exists()
        
        if has_checkin:
            consecutive_days += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    if consecutive_days >= 7:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='streak',
            title='Неделя дисциплины',
            defaults={
                'description': 'Отмечался 7 дней подряд',
                'icon': '🔥',
                'progress': consecutive_days,
                'target': 7
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 3. Проверяем достижение "Завершил первый челлендж УСПЕШНО"
    successful_challenges = UserChallenge.objects.filter(
        user=user,
        status='completed'
    ).count()
    
    if successful_challenges >= 1:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='completion',
            title='Первый успех',
            defaults={
                'description': 'Успешно завершил первый челлендж',
                'icon': '🎯',
                'progress': successful_challenges,
                'target': 1
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 4. Проверяем достижение "Мастер разнообразия"
    categories = UserChallenge.objects.filter(user=user).values_list('category', flat=True)
    unique_categories = len(set(categories))
    
    if unique_categories >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='variety',
            title='Мастер разнообразия',
            defaults={
                'description': 'Пробовал челленджи в 3+ категориях',
                'icon': '🌈',
                'progress': unique_categories,
                'target': 3
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 5. Проверяем достижение "5 челленджей завершено"
    if successful_challenges >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='completion',
            title='Опытный игрок',
            defaults={
                'description': 'Успешно завершил 5 челленджей',
                'icon': '🏅',
                'progress': successful_challenges,
                'target': 5
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 6. Проверяем достижение "Месяц активности"
    from django.contrib.auth.models import User
    user_obj = User.objects.get(username=user.username)
    days_since_join = (timezone.now() - user_obj.date_joined).days
    
    if days_since_join >= 30:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='consistency',
            title='Месяц с нами',
            defaults={
                'description': 'Ты с нами уже 30 дней!',
                'icon': '📅',
                'progress': days_since_join,
                'target': 30
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 7. Проверяем достижение "100 дней отметок"
    total_checkins = DailyCheckin.objects.filter(
        user_challenge__user=user,
        is_completed=True
    ).count()
    
    if total_checkins >= 100:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='streak',
            title='Сотня отметок',
            defaults={
                'description': 'Сделал 100 отметок выполнения',
                'icon': '💯',
                'progress': total_checkins,
                'target': 100
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 8. Проверяем достижение "Суперсерия" (максимальная серия за все время)
    all_checkin_dates = DailyCheckin.objects.filter(
        user_challenge__user=user,
        is_completed=True
    ).values_list('date', flat=True).order_by('date').distinct()
    
    max_streak = 0
    if all_checkin_dates:
        dates_list = list(all_checkin_dates)
        current_streak = 1
        
        for i in range(1, len(dates_list)):
            prev_date = dates_list[i-1]
            curr_date = dates_list[i]
            
            if (curr_date - prev_date).days == 1:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
        
        max_streak = max(max_streak, current_streak)
    
    if max_streak >= 30:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='streak',
            title='Суперсерия',
            defaults={
                'description': '30 дней подряд без пропусков',
                'icon': '⚡',
                'progress': max_streak,
                'target': 30
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 9. Проверяем достижение "Марафонец" (длинный челлендж)
    long_challenges = UserChallenge.objects.filter(
        user=user,
        custom_duration__gte=90
    ).count()
    
    if long_challenges >= 1:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='consistency',
            title='Марафонец',
            defaults={
                'description': 'Начал челлендж на 90+ дней',
                'icon': '🏃‍♂️',
                'progress': long_challenges,
                'target': 1
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 10. Проверяем достижение "Идеальное выполнение" (челлендж на 100%)
    perfect_challenges = UserChallenge.objects.filter(
        user=user,
        status='completed',
        completed_days=F('duration_days')
    ).count()
    
    if perfect_challenges >= 1:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='completion',
            title='Идеальное выполнение',
            defaults={
                'description': 'Завершил челлендж на 100%',
                'icon': '⭐',
                'progress': perfect_challenges,
                'target': 1
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 11. Проверяем достижение "200 дней с нами"
    if days_since_join >= 200:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='consistency',
            title='Ветеран',
            defaults={
                'description': 'Ты с нами уже 200 дней!',
                'icon': '👴',
                'progress': days_since_join,
                'target': 200
            }
        )
        if created:
            achievements_created.append(achievement)
    
    # 12. Проверяем достижение "10 завершенных челленджей"
    if successful_challenges >= 10:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            type='completion',
            title='Мастер челленджей',
            defaults={
                'description': 'Успешно завершил 10 челленджей',
                'icon': '👑',
                'progress': successful_challenges,
                'target': 10
            }
        )
        if created:
            achievements_created.append(achievement)
    
    return achievements_created

def recalculate_all_achievements(user):
    """Удаляет и пересоздает все достижения пользователя"""
    from .models import Achievement
    
    deleted_count = Achievement.objects.filter(user=user).delete()[0]
    print(f"Удалено {deleted_count} старых достижений для {user.username}")
    
    new_achievements = check_and_create_achievements(user)
    
    print(f"Создано {len(new_achievements)} новых достижений для {user.username}")
    return new_achievements