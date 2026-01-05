from django.urls import include, path
from rest_framework_nested import routers
from .views import CourseViewSet, LessonViewSet, LessonBlockViewSet, DirectLessonViewSet, HomeworkSubmissionViewSet

router = routers.SimpleRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r'blocks', LessonBlockViewSet)
router.register(r"lessons", DirectLessonViewSet, basename="direct-lessons")
router.register(r'homeworks', HomeworkSubmissionViewSet, basename='homeworks')


courses_router = routers.NestedSimpleRouter(router, r"courses", lookup="course")
courses_router.register(r"lessons", LessonViewSet, basename="course-lessons")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(courses_router.urls)),
]
