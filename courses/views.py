from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
# Импортируем стандартные пермишены. IsAdminOrReadOnly заменим на комбинацию.
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly

from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import HomeworkSubmission
from .serializers import HomeworkSubmissionSerializer

from .models import Course, Lesson, Enrollment, UserLessonProgress, LessonBlock
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    LessonSerializer, LessonBlockSerializer,
)

# Если у тебя реально есть этот файл - раскомментируй. Если нет - используй IsAdminUser
# from config.permissions import IsAdminOrReadOnly

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_published=True)

    # Вместо IsAdminOrReadOnly используем стандартную логику:
    # Читать могут все, менять - только Админ.
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['my_courses', 'enroll']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        return CourseDetailSerializer if self.action == "retrieve" else CourseListSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({"detail": "Вы уже записаны на этот курс."}, status=400)
        Enrollment.objects.create(user=user, course=course)
        return Response({"detail": "Вы успешно записаны на курс."}, status=201)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        enrolled_course_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        queryset = Course.objects.filter(id__in=enrolled_course_ids) # Исправил get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    # Тоже заменим IsAdminOrReadOnly на стандартное
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'context']:
            return [IsAuthenticated()] # Уроки видят только зарегистрированные
        if self.action in ['complete', 'check_quiz']:
            return [IsAuthenticated()]
        return [IsAdminUser()] # Создавать/удалять уроки может только админ

    def perform_create(self, serializer):
        # Достаем ID курса из URL и привязываем урок
        course_id = self.kwargs.get("course_pk")
        course = get_object_or_404(Course, pk=course_id)
        serializer.save(course=course)

    def get_queryset(self):
        if "course_pk" not in self.kwargs:
            return Lesson.objects.none()
        course_id = self.kwargs["course_pk"]
        return Lesson.objects.filter(course_id=course_id).order_by("order", "id")

    @action(detail=True, methods=["get"])
    def context(self, request, course_pk=None, pk=None):
        course = get_object_or_404(Course, pk=course_pk)
        lessons = list(Lesson.objects.filter(course=course).order_by("order", "id"))
        try:
            current_lesson_id = int(pk)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid Lesson ID"}, status=400)

        idx = next((i for i, l in enumerate(lessons) if l.id == current_lesson_id), None)
        if idx is None:
            return Response({"detail": "Lesson not found in this course"}, status=404)

        lesson = lessons[idx]
        prev_lesson = lessons[idx - 1] if idx > 0 else None
        next_lesson = lessons[idx + 1] if idx < len(lessons) - 1 else None

        return Response({
            "course": CourseDetailSerializer(course, context={'request': request}).data,
            "lesson": LessonSerializer(lesson, context={'request': request}).data,
            "prevLesson": LessonSerializer(prev_lesson, context={'request': request}).data if prev_lesson else None,
            "nextLesson": LessonSerializer(next_lesson, context={'request': request}).data if next_lesson else None,
        })

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def check_quiz(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        user = request.user

        # 1. Получаем ответы студента из запроса
        # Ожидаем формат: { "1": "A", "2": "C", ... }
        student_answers = request.data.get('answers', {})

        # 2. Находим блок с тестом (quiz)
        quiz_block = lesson.blocks.filter(type='quiz').first()
        if not quiz_block:
            return Response({"detail": "В этом уроке нет теста"}, status=400)
        # 3. Достаем правильные ответы из базы (они лежат в quiz_block.data['correct_answers'])
        correct_answers = quiz_block.data.get('correct_answers', {})

        if not correct_answers:
            return Response({"detail": "Ключи к тесту не заданы преподавателем"}, status=500)

        # 4. Считаем баллы
        score = 0
        total_questions = len(correct_answers)

        for q_num, correct_opt in correct_answers.items():
            # Сравниваем ответ студента (приводим к строке на всякий случай)
            if str(student_answers.get(q_num)) == str(correct_opt):
                score += 1

        # 5. Сохраняем прогресс и оценку
        progress, _ = UserLessonProgress.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={
                'status': 'completed',
                'completed_at': timezone.now()
                # Если у тебя есть поле score в модели Progress, добавь его сюда:
                # 'score': score
            }
        )

        # Открываем следующий урок (как в методе complete)
        # ... (твоя логика открытия следующего урока) ...

        return Response({
            "score": score,
            "total": total_questions,
            "passed": True, # Можно добавить логику: passed = score > total * 0.7
            "detail": f"Вы набрали {score} из {total_questions} баллов!"
        })

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        user = request.user
        if not Enrollment.objects.filter(user=user, course=lesson.course).exists():
            return Response({"detail": "Вы не записаны на этот курс."}, status=403)

        UserLessonProgress.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={'status': 'completed', 'completed_at': timezone.now()}
        )
        lessons = list(Lesson.objects.filter(course=lesson.course).order_by("order", "id"))
        try:
            current_lesson_index = lessons.index(lesson)
            if current_lesson_index < len(lessons) - 1:
                next_lesson = lessons[current_lesson_index + 1]
                obj, created = UserLessonProgress.objects.get_or_create(
                    user=user,
                    lesson=next_lesson,
                    defaults={'status': 'active'}
                )
                if not created and obj.status == 'locked':
                    obj.status = 'active'
                    obj.save()
        except ValueError:
            pass
        return Response({"detail": "Урок завершен.", "status": "completed"}, status=200)


# --- ВОТ ОН, НОВЫЙ ГЕРОЙ ---
class LessonBlockViewSet(viewsets.ModelViewSet):
    queryset = LessonBlock.objects.all()
    serializer_class = LessonBlockSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]


class DirectLessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAdminUser] # Строго только для админов
    # Разрешаем только чтение и обновление (создание оставим через курс)
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSubmissionSerializer
    parser_classes = (MultiPartParser, FormParser)
    # Важно: подключить пермишены
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Админ видит ВСЕ работы
        if self.request.user.is_staff:
            return HomeworkSubmission.objects.all().order_by('-created_at')
        # Студент видит ТОЛЬКО свои
        return HomeworkSubmission.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)