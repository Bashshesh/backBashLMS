from rest_framework import serializers
from .models import Course, Lesson, Enrollment, UserLessonProgress, LessonBlock, HomeworkSubmission


# --- 1. Сериалайзер для Блоков (Без изменений) ---
class LessonBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonBlock
        fields = ['id', 'lesson', 'type', 'order', 'content', 'file', 'data', 'is_hidden']


# --- 2. Сериалайзер для Урока ---
class LessonSerializer(serializers.ModelSerializer):
    blocks = LessonBlockSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    # Убираем progress отсюда, так как процент прохождения урока - странная штука.
    # Обычно процент нужен только КУРСУ. Урок либо сдан (100%), либо нет (0%).

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'lesson_type', 'order', 'status', 'blocks']

    def get_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 'locked'

        # Ищем запись о прогрессе
        progress = UserLessonProgress.objects.filter(user=request.user, lesson=obj).first()
        if progress:
            return progress.status

        # Если прогресса нет, но курс куплен -> первый урок обычно открыт, остальные закрыты?
        # Или все открыты? Тут твоя бизнес-логика. Допустим, пока locked.
        # Но если ты хочешь, чтобы при покупке все открывалось, то 'active'.
        is_enrolled = Enrollment.objects.filter(user=request.user, course=obj.course).exists()
        return 'active' if is_enrolled else 'locked'


# --- 3. Сериалайзер Списка Курсов (ДЛЯ ВИДЖЕТА!) ---
class CourseListSerializer(serializers.ModelSerializer):
    is_enrolled = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField() # <--- ВОТ СЮДА ДОБАВЛЯЕМ!

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'cover', 'is_enrolled', 'price', 'progress']

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(user=request.user, course=obj).exists()
        return False

    def get_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        # 1. Считаем всего уроков в ЭТОМ курсе
        total_lessons = obj.lessons.count()
        if total_lessons == 0:
            return 0

        # 2. Считаем, сколько уроков прошел ЭТОТ юзер в ЭТОМ курсе
        completed_count = UserLessonProgress.objects.filter(
            user=request.user,
            lesson__course=obj, # Связь через урок к курсу
            status='completed'
        ).count()

        return int((completed_count / total_lessons) * 100)


# --- 4. Детальный Сериалайзер Курса ---
class CourseDetailSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField() # <--- Сюда тоже полезно добавить!

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'cover', 'lessons', 'is_enrolled', 'price', 'progress']

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(user=request.user, course=obj).exists()
        return False

    # Копипаст логики прогресса (можно вынести в миксин, но пока так проще)
    def get_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        total_lessons = obj.lessons.count()
        if total_lessons == 0: return 0

        completed_count = UserLessonProgress.objects.filter(
            user=request.user,
            lesson__course=obj,
            status='completed'
        ).count()

        return int((completed_count / total_lessons) * 100)


# --- 5. ДЗ (Без изменений) ---
class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'lesson', 'lesson_title', 'user', 'user_email', 'file', 'comment', 'created_at', 'grade']
        read_only_fields = ['grade', 'created_at', 'user', 'user_email', 'lesson_title']
