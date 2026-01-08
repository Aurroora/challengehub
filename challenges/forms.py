from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserChallenge, DailyCheckin

# Формы для пользователей
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтвердите пароль'})

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email']

# Формы для челленджей
class StartChallengeForm(forms.ModelForm):
    """Форма для начала челленджа"""
    class Meta:
        model = UserChallenge
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваши заметки на старте...'
            }),
        }

class DailyCheckinForm(forms.ModelForm):
    """Форма для ежедневной отметки"""
    class Meta:
        model = DailyCheckin
        fields = ['is_completed', 'notes', 'rating']
        widgets = {
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Как прошел день?'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

class CustomChallengeForm(forms.ModelForm):
    """Форма для создания своего челленджа"""
    class Meta:
        model = UserChallenge
        fields = ['custom_title', 'custom_description', 'custom_category', 'custom_duration', 'notes']
        widgets = {
            'custom_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название вашего челленджа'
            }),
            'custom_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание челленджа...'
            }),
            'custom_category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'custom_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество дней'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки...'
            }),
        }