from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from courses.models import Enrollment, Course

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    enrolled_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'date_joined', 'courses_count', 'enrolled_courses']

    def get_courses_count(self, obj):
        return Enrollment.objects.filter(user=obj).count()

    def get_enrolled_courses(self, obj):
        enrollments = Enrollment.objects.filter(user=obj).select_related('course')
        return [
            {'id': e.course.id, 'title': e.course.title}
            for e in enrollments
        ]


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_staff']

class AssignCourseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    course_id = serializers.IntegerField()

def validate(self, data):
    if not User.objects.filter(id=data['user_id']).exists():
        raise serializers.ValidationError("Пользователь не найден")
    if not Course.objects.filter(id=data['course_id']).exists():
        raise serializers.ValidationError("Курс не найден")
    if Enrollment.objects.filter(user_id=data['user_id'], course_id=data['course_id']).exists():
        raise serializers.ValidationError("Этот пользователь уже записан на этот курс")
    return data

def save(self):
    user = User.objects.get(id=self.validated_data['user_id'])
    course = Course.objects.get(id=self.validated_data['course_id'])
    # Создаем запись
    return Enrollment.objects.create(user=user, course=course)
