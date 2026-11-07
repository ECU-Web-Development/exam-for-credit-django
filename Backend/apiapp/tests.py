from django.test import TestCase
from .models import *
from django.contrib.auth.models import Permission, User


class TaskTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("john", "lennon@thebeatles.com", "johnpassword")
        Task.objects.create(body="New Task", description="New Desc", assigned_to=user)

    def test_task_created(self):
        task = Task.objects.get(body="New Task")
        self.assertEqual(task.description, 'New Desc')

        task.description = "New Desc2"
        task.save()
        self.assertEqual(task.description, 'New Desc2')
