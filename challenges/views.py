from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from .models import ChallengeTemplate, UserChallenge
from .forms import UserRegisterForm, UserUpdateForm
from .forms import StartChallengeForm, CustomChallengeForm
from django.utils.timezone import now
from .models import ChallengeTemplate, UserChallenge, DailyCheckin
from datetime import timedelta

def home(request):
    """Главная страница"""
    # Получаем 3 случайных активных челленджа для показа на главной
    featured_challenges = ChallengeTemplate.objects.filter(is_active=True).order_by('?')[:3]
    return render(request, 'challenges/home.html', {'featured_challenges': featured_challenges})

def challenge_list(request):
    """Список всех шаблонов челленджей"""
    challenges = ChallengeTemplate.objects.filter(is_active=True)
    
    # Фильтрация по категории
    category = request.GET.get('category')
    if category:
        challenges = challenges.filter(category=category)
    
    # Сортировка
    sort = request.GET.get('sort', 'title')
    if sort == 'difficulty':
        challenges = challenges.order_by('difficulty')
    elif sort == 'duration':
        challenges = challenges.order_by('duration_days')
    else:
        challenges = challenges.order_by('title')
    
    return render(request, 'challenges/challenge_list.html', {'challenges': challenges})

def challenge_detail(request, pk):
    """Детальная страница челленджа"""
    challenge = get_object_or_404(ChallengeTemplate, pk=pk, is_active=True)
    
    # Проверяем, запустил ли пользователь этот челлендж
    user_challenge = None
    if request.user.is_authenticated:
        user_challenge = UserChallenge.objects.filter(
            user=request.user, 
            template=challenge,
            status='active'
        ).first()
    
    return render(request, 'challenges/challenge_detail.html', {
        'challenge': challenge,
        'user_challenge': user_challenge
    })

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически логиним пользователя после регистрации
            username = form.cleaned_data.get('username')
            messages.success(request, f'Добро пожаловать, {username}! Ваш аккаунт создан.')
            return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'challenges/register.html', {'form': form})

@login_required
def profile(request):
    """Личный кабинет пользователя"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
    
    # Получаем челленджи пользователя
    user_challenges = UserChallenge.objects.filter(user=request.user)
    
    # Статистика
    active_challenges = user_challenges.filter(status='active').count()
    completed_challenges = user_challenges.filter(status='completed').count()
    total_days_completed = sum(challenge.completed_days for challenge in user_challenges)
    
    return render(request, 'challenges/profile.html', {
        'user_form': user_form,
        'user_challenges': user_challenges,
        'active_challenges': active_challenges,
        'completed_challenges': completed_challenges,
        'total_days_completed': total_days_completed,
    })

@login_required
def start_challenge(request, pk):
    """Начать челлендж"""
    challenge = get_object_or_404(ChallengeTemplate, pk=pk, is_active=True)
    
    # Проверяем, не начал ли уже пользователь этот челлендж
    existing_challenge = UserChallenge.objects.filter(
        user=request.user,
        template=challenge,
        status='active'
    ).first()
    
    if existing_challenge:
        messages.info(request, 'Вы уже участвуете в этом челлендже!')
        return redirect('challenge_detail', pk=pk)
    
    if request.method == 'POST':
        # Простая форма без использования forms.py
        notes = request.POST.get('notes', '')
        
        user_challenge = UserChallenge.objects.create(
            user=request.user,
            template=challenge,
            status='active',
            notes=notes,
            start_date=now().date()
        )
        
        messages.success(request, f'Челлендж "{challenge.title}" начат! Удачи!')
        return redirect('profile')
    
    return render(request, 'challenges/start_challenge.html', {
        'challenge': challenge
    })

@login_required
def create_custom_challenge(request):
    """Создать свой челлендж"""
    if request.method == 'POST':
        form = CustomChallengeForm(request.POST)
        if form.is_valid():
            user_challenge = form.save(commit=False)
            user_challenge.user = request.user
            user_challenge.status = 'active'
            user_challenge.start_date = now().date()
            user_challenge.save()
            
            messages.success(request, 'Ваш челлендж создан!')
            return redirect('profile')
    else:
        form = CustomChallengeForm()
    
    return render(request, 'challenges/create_custom.html', {'form': form})

@login_required
def daily_checkin(request, challenge_id):
    """Ежедневная отметка"""
    user_challenge = get_object_or_404(UserChallenge, pk=challenge_id, user=request.user)
    
    today = now().date()
    existing_checkin = DailyCheckin.objects.filter(
        user_challenge=user_challenge,
        date=today
    ).first()
    
    # Если уже есть отметка на сегодня и это GET запрос
    if existing_checkin and request.method == 'GET':
        messages.info(request, 'Вы уже отметились сегодня. Можете отредактировать отметку.')
    
    if request.method == 'POST':
        is_completed = request.POST.get('is_completed') == 'true'
        rating = request.POST.get('rating')
        notes = request.POST.get('notes', '')
        
        if existing_checkin:
            # Обновляем существующую отметку
            was_completed = existing_checkin.is_completed
            existing_checkin.is_completed = is_completed
            existing_checkin.rating = int(rating) if rating else None
            existing_checkin.notes = notes
            existing_checkin.save()
            
            # Обновляем счетчик дней
            if is_completed and not was_completed:
                user_challenge.completed_days += 1
            elif not is_completed and was_completed:
                user_challenge.completed_days -= 1
        else:
            # Создаем новую отметку
            checkin = DailyCheckin.objects.create(
                user_challenge=user_challenge,
                date=today,
                is_completed=is_completed,
                rating=int(rating) if rating else None,
                notes=notes
            )
            
            # Увеличиваем счетчик только если выполнено
            if is_completed:
                user_challenge.completed_days += 1
        
        # Рассчитываем текущую серию
        streak = 0
        checkins = user_challenge.checkins.filter(is_completed=True).order_by('-date')
        for checkin_day in checkins:
            streak += 1
        user_challenge.current_streak = streak
        
        user_challenge.save()
        
        messages.success(request, 'Отметка сохранена!')
        return redirect('profile')
    
    return render(request, 'challenges/daily_checkin.html', {
        'user_challenge': user_challenge,
        'today': today,
        'existing_checkin': existing_checkin
    })

@login_required
def complete_challenge(request, challenge_id):
    """Завершить челлендж досрочно"""
    user_challenge = get_object_or_404(UserChallenge, pk=challenge_id, user=request.user)
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            user_challenge.status = 'completed'
            user_challenge.save()
            messages.success(request, f'Челлендж "{user_challenge.title}" завершен!')
            return redirect('profile')
        else:
            messages.info(request, 'Отмена завершения челленджа.')
            return redirect('profile')
    
    return render(request, 'challenges/complete_challenge.html', {
        'user_challenge': user_challenge
    })

@login_required
def challenge_calendar(request, challenge_id):
    """Календарь прогресса челленджа"""
    user_challenge = get_object_or_404(UserChallenge, pk=challenge_id, user=request.user)
    
    # Создаем данные для календаря
    calendar_data = []
    start_date = user_challenge.start_date
    end_date = user_challenge.end_date or (start_date + timedelta(days=user_challenge.duration_days))
    
    current_date = start_date
    while current_date <= end_date:
        checkin = user_challenge.checkins.filter(date=current_date).first()
        calendar_data.append({
            'date': current_date,
            'is_completed': checkin.is_completed if checkin else False,
            'rating': checkin.rating if checkin else None,
            'notes': checkin.notes if checkin else ''
        })
        current_date += timedelta(days=1)
    
    return render(request, 'challenges/challenge_calendar.html', {
        'user_challenge': user_challenge,
        'calendar_data': calendar_data
    })