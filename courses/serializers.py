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
        print(f"DEBUG: Lesson {obj.id}, User {self.context.get('request').user}")

        if not request or not request.user.is_authenticated:
            return 'BANANA' # 🍌

        # 1. Если есть запись в прогрессе — верим ей
        progress = UserLessonProgress.objects.filter(user=request.user, lesson=obj).first()

        if progress:
            print(f"🔴 НАЙДЕН ПРОГРЕСС! Урок {obj.id}, Статус: {progress.status}")
        else:
            print(f"🟢 Прогресса нет для урока {obj.id}")

        if progress:
            return progress.status

        if progress:
            return progress.status  # Вернет 'completed' только если реально прошел

        # 2. Если записи НЕТ, значит урок точно НЕ 'completed'.
        # Проверяем, куплен ли курс
        is_enrolled = Enrollment.objects.filter(user=request.user, course=obj.course).exists()

        if not is_enrolled:
            return 'locked'

        # 3. Курс куплен. Определяем, доступен ли урок.

        # Это ПЕРВЫЙ урок курса?
        # (Ищем урок с минимальным порядковым номером в этом курсе)
        first_lesson = Lesson.objects.filter(course=obj.course).order_by('order', 'id').first()

        if first_lesson and obj.id == first_lesson.id:
            return 'active'  # Первый урок всегда открыт для ученика

        # Это НЕ первый урок. Проверяем ПРЕДЫДУЩИЙ.
        # Ищем ближайший урок с order меньше текущего
        prev_lesson = Lesson.objects.filter(course=obj.course, order__lt=obj.order).order_by('-order').first()

        if prev_lesson:
            # Урок открыт ТОЛЬКО если предыдущий COMPLETED
            prev_progress = UserLessonProgress.objects.filter(
                user=request.user,
                lesson=prev_lesson,
                status='completed'
            ).exists()

            if prev_progress:
                return 'active'

        # Во всех остальных случаях
        return 'locked'



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
