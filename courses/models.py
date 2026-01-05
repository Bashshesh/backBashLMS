from django.db import models
from django.conf import settings

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    cover = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

#new model of lessons AHHAHAHAHAHAHAH
class Lesson(models.Model):
    LESSON_TYPES = [
        ('kazakh', 'Kazakh (Lecture)'),
        ('math', 'Math (Test & Review)'),
        ('custom', 'Custom'),
    ]

    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True) # Краткое описание в списке уроков

    # Этот тип нужен ФРОНТЕНДУ, чтобы знать, какой шаблон конструктора открыть учителю
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='custom')

    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Если это новый урок (нет id) и порядок не задан (или 0)
        if not self.pk and not self.order:
            # Ищем максимальный order среди уроков ЭТОГО курса
            last_lesson = Lesson.objects.filter(course=self.course).order_by('-order').first()
            if last_lesson:
                self.order = last_lesson.order + 1
            else:
                self.order = 1
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

#for front nahui
class LessonBlock(models.Model):
    BLOCK_TYPES = [
        ('text', 'Text / HTML'),
        ('video', 'Video File'),
        ('pdf', 'PDF File'),
        ('quiz', 'Quiz Config'), # Таймер, настройки теста
        ('homework', 'Homework Config'), # Настройки домашки
        ('upload', 'File Upload'), # Просто файл для скачивания (методичка)
    ]

    lesson = models.ForeignKey(Lesson, related_name='blocks', on_delete=models.CASCADE)

    # Тип кубика
    type = models.CharField(max_length=20, choices=BLOCK_TYPES)

    # Порядок внутри урока (1, 2, 3...)
    order = models.PositiveIntegerField(default=0)

    # 1. Текстовый контент (если type='text')
    content = models.TextField(blank=True, null=True)

    # 2. Файл (если type='video', 'pdf', 'upload')
    # Файлы будут лежать в папке: media/lessons/2025/12/27/filename.mp4
    file = models.FileField(upload_to='lessons/files/%Y/%m/%d/', blank=True, null=True)

    # 3. JSON настройки (для 'quiz', 'homework' и мета-данных видео)
    # Например: { "timer": 60, "video_label": "Задачи 1-10" }
    data = models.JSONField(default=dict, blank=True)

    #4. Is hidden для видео-разборов и спрятать их
    is_hidden = models.BooleanField(default=False, verbose_name="Скрыт до завершения")


    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Block {self.type} for {self.lesson.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Подписка на курс'
        verbose_name_plural = 'Подписки на курсы'

    def __str__(self):
        return f"{self.user.email} enrolled in {self.course.title}"


class UserLessonProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'Заблокирован'),
        ('active', 'Активен'),
        ('completed', 'Завершен'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='locked')
    completed_at = models.DateTimeField(null=True, blank=True)
    grade = models.IntegerField(null=True, blank=True) # Для оценки, если есть ДЗ

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name = 'Прогресс урока'
        verbose_name_plural = 'Прогресс уроков'

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} ({self.status})"


class HomeworkSubmission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='homeworks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='homework_submissions')
    file = models.FileField(upload_to='homeworks/%Y/%m/%d/')
    comment = models.TextField(blank=True, null=True) # Если ученик хочет что-то написать
    created_at = models.DateTimeField(auto_now_add=True)
    grade = models.IntegerField(null=True, blank=True) # Оценка админа (опционально)

    def __str__(self):
        return f"{self.user} - {self.lesson}"