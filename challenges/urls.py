from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.home, name='home'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/<int:pk>/', views.challenge_detail, name='challenge_detail'),
    path('challenges/<int:pk>/start/', views.start_challenge, name='start_challenge'),
    path('challenges/create-custom/', views.create_custom_challenge, name='create_custom'),
    
    # Управление челленджами пользователя
    path('my-challenges/<int:challenge_id>/checkin/', views.daily_checkin, name='daily_checkin'),
    path('my-challenges/<int:challenge_id>/complete/', views.complete_challenge, name='complete_challenge'),
    path('my-challenges/<int:challenge_id>/calendar/', views.challenge_calendar, name='challenge_calendar'),  # ← ЭТА СТРОКА
    
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='challenges/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile, name='profile'),
]