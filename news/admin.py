from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'id', 'image') # Что показывать в списке
    search_fields = ('title', 'content')   # Поиск
    list_filter = ('date',)                # Фильтр справа
    fields = ('id', 'title', 'content', 'image')
