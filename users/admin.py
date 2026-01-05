from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Настраиваем отображение полей, так как у нас email вместо username
    list_display = ('email', 'username', 'phone', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'phone')
    ordering = ('email',)

    # Поля при редактировании пользователя
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'phone')}), # Добавили phone
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
