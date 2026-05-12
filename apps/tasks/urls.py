from django.urls import path
from apps.tasks.views import TaskView, TaskDetailView, DeletedTaskView, TaskReactivateView, TasksByProjectView

urlpatterns = [
    path('tasks', TaskView.as_view(), name='tasks'),
    path('projects/<uuid:project_id>/deleted_tasks', DeletedTaskView.as_view(), name='tasks_deleted'),
    path('tasks/<uuid:task_id>', TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<uuid:task_id>/reactivate', TaskReactivateView.as_view(), name='task_reactivate'),
    path('projects/<uuid:project_id>/tasks', TasksByProjectView.as_view(), name='tasks_by_project'),
]
