from django.urls import path
from apps.projects.views import ProjectView, ProjectDetailView, ProjectMembersView, ProjectsByWorkspaceView

urlpatterns = [
    path('projects', ProjectView.as_view(), name='projects'),
    path('projects/<uuid:project_id>', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<uuid:project_id>/members', ProjectMembersView.as_view(), name='project_members'),
    path('workspaces/<uuid:workspace_id>/projects', ProjectsByWorkspaceView.as_view(), name='projects_by_workspace'),
]
