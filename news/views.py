from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import News
from .serializers import NewsSerializer

class NewsViewSet(ReadOnlyModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
