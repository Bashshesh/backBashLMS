from django.urls import path, include
from rest_framework.routers import DefaultRouter # <--- 1. Берем стандартный роутер
from .views import RegisterView, MeView, AdminUserViewSet, AdminStatsView

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),

    path('', include(router.urls)),
]
