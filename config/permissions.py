from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает доступ на запись (POST, PUT, DELETE) только администраторам (is_staff=True).
    Разрешает доступ на чтение (GET, HEAD, OPTIONS) всем.
    """

    def has_permission(self, request, view):
        # Разрешить чтение всем (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешить запись только администраторам
        return request.user and request.user.is_staff
