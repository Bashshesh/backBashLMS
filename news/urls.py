from rest_framework.routers import SimpleRouter
from .views import NewsViewSet

router = SimpleRouter()
router.register(r"news", NewsViewSet, basename="news")

urlpatterns = router.urls
