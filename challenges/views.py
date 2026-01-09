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
import plotly.graph_objects as go
import plotly.offline as opy
import pandas as pd
import random
from datetime import datetime, timedelta

def home(request):
    """Главная страница"""
    featured_challenges = ChallengeTemplate.objects.filter(is_active=True).order_by('?')[:3]
    return render(request, 'challenges/home.html', {'featured_challenges': featured_challenges})

def challenge_list(request):
    """Список всех шаблонов челленджей"""
    challenges = ChallengeTemplate.objects.filter(is_active=True)
    
    category = request.GET.get('category')
    if category:
        challenges = challenges.filter(category=category)
    
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
            login(request, user)
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
    
    user_challenges = UserChallenge.objects.filter(user=request.user).order_by(
        '-status',
        '-start_date'
    )
    
    active_challenges = user_challenges.filter(status='active').count()
    completed_challenges = user_challenges.filter(status='completed').count()
    
    return render(request, 'challenges/profile.html', {
        'user_form': user_form,
        'user_challenges': user_challenges,
        'active_challenges': active_challenges,
        'completed_challenges': completed_challenges,
    })

@login_required
def start_challenge(request, pk):
    """Начать челлендж"""
    challenge = get_object_or_404(ChallengeTemplate, pk=pk, is_active=True)
    
    existing_challenge = UserChallenge.objects.filter(
        user=request.user,
        template=challenge,
        status='active'
    ).first()
    
    if existing_challenge:
        messages.info(request, 'Вы уже участвуете в этом челлендже!')
        return redirect('challenge_detail', pk=pk)
    
    if request.method == 'POST':
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
        print("POST запрос получен")
        form = CustomChallengeForm(request.POST)
        if form.is_valid():
            print("Форма валидна")
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
    
    if user_challenge.status != 'active':
        messages.error(request, 'Этот челлендж уже завершен или отменен.')
        return redirect('profile')
    
    today = now().date()
    existing_checkin = DailyCheckin.objects.filter(
        user_challenge=user_challenge,
        date=today
    ).first()
    
    if existing_checkin and request.method == 'GET':
        messages.info(request, 'Вы уже отметились сегодня. Можете отредактировать отметку.')
    
    if request.method == 'POST':
        is_completed = request.POST.get('is_completed') == 'true'
        rating = request.POST.get('rating')
        notes = request.POST.get('notes', '')
        
        if existing_checkin:
            was_completed = existing_checkin.is_completed
            existing_checkin.is_completed = is_completed
            existing_checkin.rating = int(rating) if rating else None
            existing_checkin.notes = notes
            existing_checkin.save()
            
            if is_completed and not was_completed:
                user_challenge.completed_days += 1
            elif not is_completed and was_completed:
                user_challenge.completed_days -= 1
        else:
            checkin = DailyCheckin.objects.create(
                user_challenge=user_challenge,
                date=today,
                is_completed=is_completed,
                rating=int(rating) if rating else None,
                notes=notes
            )
            
            if is_completed:
                user_challenge.completed_days += 1
        
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
    
    if user_challenge.status != 'active':
        messages.error(request, 'Этот челлендж уже завершен или отменен.')
        return redirect('profile')
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            user_challenge.status = 'completed'
            user_challenge.save()
            
            messages.success(request, f'Челлендж "{user_challenge.title}" завершен! Прогресс: {user_challenge.completion_percentage}%')
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

def get_motivational_quote():
    """Мотивационные цитаты для пользователей"""
    quotes = [
        {
            'text': 'Неважно, как медленно ты продвигаешься. Главное — не останавливайся.',
            'author': 'Брюс Ли',
            'icon': '💪'
        },
        {
            'text': 'Успех — это способность двигаться от неудачи к неудаче, не теряя энтузиазма.',
            'author': 'Уинстон Черчилль',
            'icon': '🚀'
        },
        {
            'text': 'Единственный способ сделать что-то очень хорошо — любить то, что ты делаешь.',
            'author': 'Стив Джобс', 
            'icon': '❤️'
        },
        {
            'text': 'Маленькие ежедневные улучшения со временем приводят к ошеломительным результатам.',
            'author': 'Неизвестно',
            'icon': '📈'
        },
    ]
    return random.choice(quotes)

def get_category_recommendation(category):
    """Рекомендации по категориям челленджей"""
    recommendations = {
        'sport': {
            'title': 'Спортивные рекомендации',
            'tips': [
                'Начинайте с разминки 5-10 минут',
                'Пейте воду до, во время и после тренировки',
                'Слушайте свое тело - не перегружайтесь'
            ]
        },
        'study': {
            'title': 'Рекомендации по обучению',
            'tips': [
                'Используйте технику Помодоро (25/5)',
                'Делайте конспекты от руки',
                'Повторяйте материал через день'
            ]
        },
        'health': {
            'title': 'Рекомендации по здоровью',
            'tips': [
                'Спите 7-8 часов в сутки',
                'Ешьте больше овощей и фруктов',
                'Пейте 1.5-2 литра воды в день'
            ]
        },
        'creative': {
            'title': 'Творческие рекомендации',
            'tips': [
                'Выделяйте время для творчества утром',
                'Не бойтесь экспериментировать',
                'Делайте наброски и черновики'
            ]
        },
        'productivity': {
            'title': 'Рекомендации по продуктивности',
            'tips': [
                'Планируйте день с вечера',
                'Делайте самые сложные задачи утром',
                'Используйте матрицу Эйзенхауэра'
            ]
        }
    }
    return recommendations.get(category, {
        'title': 'Общие рекомендации',
        'tips': ['Будьте последовательны', 'Отслеживайте прогресс', 'Награждайте себя за успехи']
    })

@login_required
def challenge_statistics(request, challenge_id):
    """Статистика конкретного челленджа с графиками"""
    user_challenge = get_object_or_404(UserChallenge, pk=challenge_id, user=request.user)
    
    checkins = user_challenge.checkins.all().order_by('date')
    
    if not checkins:
        return render(request, 'challenges/statistics.html', {
            'user_challenge': user_challenge,
            'has_data': False,
            'message': 'Нет данных для анализа. Сделайте первую отметку!'
        })
    
    dates = []
    ratings = []
    completed = []
    notes_lengths = []
    
    for checkin in checkins:
        dates.append(checkin.date)
        ratings.append(checkin.rating if checkin.rating else 0)
        completed.append(1 if checkin.is_completed else 0)
        notes_lengths.append(len(checkin.notes) if checkin.notes else 0)
    
    graphs = []
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=dates, 
        y=ratings,
        mode='lines+markers',
        name='Оценка дня',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    fig1.update_layout(
        title='Динамика оценок',
        xaxis_title='Дата',
        yaxis_title='Оценка (1-5)',
        template='plotly_white',
        height=350
    )
    graphs.append(('Оценки', opy.plot(fig1, auto_open=False, output_type='div')))
    
    fig2 = go.Figure(data=[
        go.Bar(
            x=dates,
            y=completed,
            name='Выполнено',
            marker_color=['#28a745' if x == 1 else '#dc3545' for x in completed]
        )
    ])
    fig2.update_layout(
        title='✅ Выполнение по дням',
        xaxis_title='Дата',
        yaxis_title='Выполнено (1) / Не выполнено (0)',
        template='plotly_white',
        height=350
    )
    graphs.append(('📅 Выполнение', opy.plot(fig2, auto_open=False, output_type='div')))
    
    total_days = len(completed)
    completed_days = sum(completed)
    completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
    
    ratings_with_values = [r for r in ratings if r > 0]
    avg_rating = sum(ratings_with_values) / len(ratings_with_values) if ratings_with_values else 0
    
    current_streak = 0
    max_streak = 0
    temp_streak = 0
    
    for comp in reversed(completed):
        if comp == 1:
            temp_streak += 1
            if temp_streak > max_streak:
                max_streak = temp_streak
        else:
            break
    
    current_streak = temp_streak
    
    statistics = {
        'total_days': total_days,
        'completed_days': completed_days,
        'completion_rate': round(completion_rate, 1),
        'avg_rating': round(avg_rating, 2),
        'current_streak': current_streak,
        'max_streak': max_streak,
        'total_notes_chars': sum(notes_lengths),
        'avg_notes_length': round(sum(notes_lengths) / len([x for x in notes_lengths if x > 0]), 1) if any(notes_lengths) else 0,
    }
    
    category_recommendation = get_category_recommendation(user_challenge.category)
    motivational_quote = get_motivational_quote()
    
    return render(request, 'challenges/statistics.html', {
        'user_challenge': user_challenge,
        'graphs': graphs,
        'statistics': statistics,
        'category_recommendation': category_recommendation,
        'motivational_quote': motivational_quote,
        'has_data': True
    })

@login_required
def overall_statistics(request):
    """Общая статистика пользователя"""
    user_challenges = UserChallenge.objects.filter(user=request.user)
    
    if not user_challenges:
        return render(request, 'challenges/overall_stats.html', {
            'has_data': False,
            'message': 'У вас пока нет челленджей для анализа.'
        })
    
    data = []
    total_unique_days = set()
    
    for challenge in user_challenges:
        checkins = challenge.checkins.all()
        if checkins:
            completed_days = checkins.filter(is_completed=True).count()
            total_days = checkins.count()
            completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
            
            for checkin in checkins:
                total_unique_days.add(checkin.date)
            
            data.append({
                'title': challenge.title,
                'category': challenge.category,
                'completion_rate': completion_rate,
                'duration': challenge.duration_days,
                'status': challenge.status,
                'start_date': challenge.start_date,
                'streak': challenge.current_streak,
                'actual_days': total_days,
                'completed_days': completed_days,
            })
    
    if not data:
        return render(request, 'challenges/overall_stats.html', {
            'has_data': False,
            'message': 'Нет данных по челленджам для анализа.'
        })
    
    df = pd.DataFrame(data)
    
    graphs = []
    
    fig1 = go.Figure(data=[
        go.Bar(
            x=df['title'].str[:20],
            y=df['completion_rate'],
            marker_color='lightblue',
            text=df['completion_rate'].round(1).astype(str) + '%',
            textposition='auto',
            width=0.6
        )
    ])
    fig1.update_layout(
        title='📊 Процент выполнения по челленджам',
        xaxis_title='Челлендж',
        yaxis_title='Процент выполнения (%)',
        template='plotly_white',
        height=450,
        margin=dict(l=50, r=50, t=80, b=150),
        xaxis_tickangle=-45
    )
    graphs.append(('Процент выполнения', opy.plot(fig1, auto_open=False, output_type='div')))
    
    category_counts = df['category'].value_counts()
    fig2 = go.Figure(data=[
        go.Pie(
            labels=[dict(ChallengeTemplate.CATEGORY_CHOICES).get(cat, cat) for cat in category_counts.index],
            values=category_counts.values,
            hole=.3,
            textinfo='label+percent',
            marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']),
            textfont=dict(size=14)
        )
    ])
    fig2.update_layout(
        title='🏷️ Распределение по категориям',
        template='plotly_white',
        height=500,
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=True,
        legend=dict(
            font=dict(size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    graphs.append(('Категории', opy.plot(fig2, auto_open=False, output_type='div')))
    
    total_challenges = len(df)
    active_challenges = len(df[df['status'] == 'active'])
    completed_challenges = len(df[df['status'] == 'completed'])
    avg_completion_rate = df['completion_rate'].mean()
    
    statistics = {
        'total_challenges': total_challenges,
        'active_challenges': active_challenges,
        'completed_challenges': completed_challenges,
        'avg_completion_rate': round(avg_completion_rate, 1),
        'total_days_tracked': len(total_unique_days),
        'total_checkins': df['actual_days'].sum(),
        'total_completed': df['completed_days'].sum(),
    }
    
    return render(request, 'challenges/overall_stats.html', {
        'graphs': graphs,
        'statistics': statistics,
        'has_data': True
    })