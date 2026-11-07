from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission, User

class Task(models.Model):
    body = models.TextField(blank=False, default="sample body")
    description = models.TextField(blank=False, default="sample task desc")
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="assigned_tasks",default=1)

    def print_desc(self):
        print(self.description)
    # def __str__(self):
    #     return self.question_text

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="notifications",default=1)
    task = models.ForeignKey(Task,on_delete=models.CASCADE,related_name="notifications")
    message = models.TextField(blank=False, default="sample notif message")

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=500)
