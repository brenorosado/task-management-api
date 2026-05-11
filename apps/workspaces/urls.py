from django.urls import path
from apps.workspaces.views import WorkspaceView, WorkspaceDetailView

urlpatterns = [
    path('workspaces', WorkspaceView.as_view(), name='workspaces'),
    path('workspaces/<uuid:workspace_id>', WorkspaceDetailView.as_view(), name='workspace_detail'),
]
