from django.contrib import admin
from .models import ChallengeTemplate, UserChallenge, DailyCheckin, Achievement

@admin.register(ChallengeTemplate)
class ChallengeTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration_days', 'difficulty_stars', 'is_active', 'created_at')
    list_filter = ('category', 'difficulty', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    
    def difficulty_stars(self, obj):
        return obj.difficulty_stars
    difficulty_stars.short_description = 'Сложность'


@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'title_display', 'category', 'start_date', 'status', 
                   'completion_percentage', 'current_streak')
    list_filter = ('status', 'start_date', 'template__category')
    search_fields = ('user__username', 'template__title', 'custom_title')
    readonly_fields = ('completion_percentage', 'days_passed', 'days_left')
    
    def title_display(self, obj):
        return obj.title
    title_display.short_description = 'Название'
    
    def category(self, obj):
        return obj.category
    category.short_description = 'Категория'


@admin.register(DailyCheckin)
class DailyCheckinAdmin(admin.ModelAdmin):
    list_display = ('user_challenge', 'date', 'is_completed', 'rating_display', 'created_at')
    list_filter = ('is_completed', 'date', 'rating')
    search_fields = ('user_challenge__user__username', 'notes')
    date_hierarchy = 'date'
    
    def rating_display(self, obj):
        if obj.rating:
            return dict(self.model.RATING_CHOICES)[obj.rating]
        return "Не оценено"
    rating_display.short_description = 'Оценка'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'is_completed', 'progress', 'target', 'earned_date')
    list_filter = ('type', 'earned_date')
    search_fields = ('user__username', 'title', 'description')
    readonly_fields = ('earned_date', 'is_completed', 'progress_percentage')