import uuid
from django.conf import settings
from django.db import models

# Create your models here.
class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'Todo'
        BLOCKED = 'blocked', 'Blocked'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='tasks')
    blocked_by = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='blocks')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_tasks')


    def __str__(self):
        return self.name