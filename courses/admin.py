from django.contrib import admin
from .models import Course, Lesson, Enrollment, LessonBlock, UserLessonProgress  # UserLessonProgress добавь, если он есть в model.py

# 1. Курсы (Объединили старое и новое)
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')

# 2. Инлайн для Блоков (Это наши Lego-кубики внутри урока)
class LessonBlockInline(admin.StackedInline):
    model = LessonBlock
    extra = 0 # Не показывать пустые формы лишний раз
    fields = ('type', 'order', 'content', 'file', 'data') # Явно указываем порядок полей

# 3. Уроки (ОЧИЩЕННАЯ ВЕРСИЯ)
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    # Убрали несуществующие поля (video_url, settings и т.д.)
    list_display = ('id', 'title', 'course', 'lesson_type', 'order', 'is_published')
    list_filter = ('course', 'lesson_type', 'is_published') # И тут тоже
    search_fields = ('title',)
    list_editable = ('order', 'is_published')

    # Подключаем блоки
    inlines = [LessonBlockInline]

# 4. Подписки (Оставляем как было)
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('user__email', 'course__title')
    date_hierarchy = 'enrolled_at'

# 5. Прогресс (Если модель UserLessonProgress существует в model.py)
# Если нет - закомментируй этот блок
@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'status', 'grade', 'completed_at')
    list_filter = ('status', 'lesson__course')
    search_fields = ('user__email', 'lesson__title')
