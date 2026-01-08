from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from .models import ChallengeTemplate, UserChallenge
from .forms import UserRegisterForm, UserUpdateForm
from .forms import StartChallengeForm, DailyCheckinForm, CustomChallengeForm
from django.utils.timezone import now

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
        form = StartChallengeForm(request.POST)
        if form.is_valid():
            user_challenge = form.save(commit=False)
            user_challenge.user = request.user
            user_challenge.template = challenge
            user_challenge.status = 'active'
            user_challenge.start_date = now().date()
            user_challenge.save()
            
            messages.success(request, f'Челлендж "{challenge.title}" начат!')
            return redirect('profile')
    else:
        form = StartChallengeForm()
    
    return render(request, 'challenges/start_challenge.html', {
        'challenge': challenge,
        'form': form
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
    
    # Проверяем, есть ли уже отметка на сегодня
    today = now().date()
    existing_checkin = DailyCheckin.objects.filter(
        user_challenge=user_challenge,
        date=today
    ).first()
    
    if request.method == 'POST':
        form = DailyCheckinForm(request.POST, instance=existing_checkin)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user_challenge = user_challenge
            checkin.date = today
            
            # Обновляем статистику челленджа
            if checkin.is_completed and not (existing_checkin and existing_checkin.is_completed):
                user_challenge.completed_days += 1
                user_challenge.current_streak += 1
            elif not checkin.is_completed and (existing_checkin and existing_checkin.is_completed):
                user_challenge.completed_days -= 1
                user_challenge.current_streak = 0
            
            checkin.save()
            user_challenge.save()
            
            messages.success(request, 'Отметка сохранена!')
            return redirect('profile')
    else:
        form = DailyCheckinForm(instance=existing_checkin)
    
    return render(request, 'challenges/daily_checkin.html', {
        'user_challenge': user_challenge,
        'form': form,
        'today': today
    })