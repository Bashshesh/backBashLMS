# courses/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from .models import Course, Lesson, Enrollment


class CourseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@test.com',
            username='testuser',
            password='test123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='Test'
        )

    def test_enroll_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/courses/{self.course.id}/enroll/')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())
