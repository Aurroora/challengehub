# challenges/management/commands/seed_challenges.py
from django.core.management.base import BaseCommand
from challenges.models import ChallengeTemplate
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Создает стандартные челленджи'

    def handle(self, *args, **kwargs):
        fixture_path = os.path.join(
            settings.BASE_DIR, 
            'challenges', 
            'fixtures', 
            'challenge_templates.json'
        )
        
        self.stdout.write(f"Ищу фикстуры по пути: {fixture_path}")
        
        if os.path.exists(fixture_path):
            self.stdout.write("Файл фикстур найден! Загружаем...")
            
            try:
                # Читаю JSON файл
                with open(fixture_path, 'r', encoding='utf-8') as f:
                    challenges_data = json.load(f)
                
                created_count = 0
                total_in_file = len(challenges_data)
                
                for item in challenges_data:
                    fields = item['fields']
                    
                    # Создаю/обновляю челлендж
                    obj, created = ChallengeTemplate.objects.get_or_create(
                        title=fields['title'],
                        defaults={
                            'description': fields['description'],
                            'category': fields['category'],
                            'duration_days': fields['duration_days'],
                            'difficulty': fields['difficulty'],
                            'is_active': fields.get('is_active', True)
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"Создан: {fields['title']}")
                    else:
                        self.stdout.write(f"Уже есть: {fields['title']}")
                
                self.stdout.write(self.style.SUCCESS(
                    f'🎉 Загружено {created_count} из {total_in_file} челленджей!'
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Ошибка загрузки фикстур: {str(e)}'
                ))
                # Создаю минимум 1 челлендж на всякий случай
                self.create_fallback_challenge()
                
        else:
            self.stdout.write(self.style.WARNING(
                f'Файл фикстур не найден! Путь: {fixture_path}'
            ))
            self.stdout.write("📁 Проверяю структуру папок...")
            
            # Отладочная информация
            for root, dirs, files in os.walk(settings.BASE_DIR):
                if 'challenge_templates.json' in files:
                    self.stdout.write(f"Найден в: {root}")
            
            # Создаю хотя бы один челлендж
            self.create_fallback_challenge()
    
    def create_fallback_challenge(self):
        """Создает базовые челленджи если фикстуры не найдены"""
        challenges = [
            {
                'title': 'Ранний подъем в 6 утра',
                'description': 'Вставайте в 6 утра каждый день для повышения продуктивности',
                'category': 'productivity',
                'duration_days': 14,
                'difficulty': 3,
            },
            {
                'title': '30 дней зарядки',
                'description': '15 минут утренней зарядки каждый день',
                'category': 'sport',
                'duration_days': 30,
                'difficulty': 1,
            },
        ]
        
        created = 0
        for data in challenges:
            obj, created_flag = ChallengeTemplate.objects.get_or_create(
                title=data['title'],
                defaults={
                    'description': data['description'],
                    'category': data['category'],
                    'duration_days': data['duration_days'],
                    'difficulty': data['difficulty'],
                    'is_active': True
                }
            )
            if created_flag:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Создано {created} стандартных челленджей'
        ))