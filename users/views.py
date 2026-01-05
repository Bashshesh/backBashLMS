from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import RegisterSerializer, UserSerializer
from django.contrib.auth import get_user_model
from .serializers import UserListSerializer, AssignCourseSerializer
from django.utils import timezone
from django.db.models import Sum
from courses.models import Course, Enrollment



User = get_user_model()

class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        total_students = User.objects.filter(is_staff=False).count()
        today = timezone.now().date()
        new_students_today = User.objects.filter(date_joined__date=today, is_staff=False).count()
        active_courses = Course.objects.filter(is_published=True).count()
        draft_courses = Course.objects.filter(is_published=False).count()
        total_revenue = Enrollment.objects.aggregate(total=Sum('course__price'))['total'] or 0

        week_ago = timezone.now() - timezone.timedelta(days=7)
        week_revenue = Enrollment.objects.filter(
            enrolled_at__gte=week_ago
        ).aggregate(total=Sum('course__price'))['total'] or 0

        return Response({
            "students": {
                "total": total_students,
                "new_today": new_students_today
            },
            "revenue": {
                "total": total_revenue,
                "week": week_revenue
            },
            "courses": {
                "active": active_courses,
                "draft": draft_courses
            }
        })



class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Только для админов: просмотр юзеров и управление ими
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser] # Точно закрываем от чужих глаз

    # Action: Выдать курс (POST /api/v1/admin/users/assign_course/)
    @action(detail=False, methods=['post'])
    def assign_course(self, request):
        serializer = AssignCourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "Course assigned successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)