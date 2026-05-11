from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.workspaces.models import Workspace
from apps.workspaces.serializers import WorkspaceSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class WorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=WorkspaceSerializer, responses=WorkspaceSerializer)
    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        
        if serializer.is_valid():
            workspace = serializer.save(owner=request.user)
            return Response(
                WorkspaceSerializer(workspace).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(responses=WorkspaceSerializer)
    def get(self, request):
        workspaces = Workspace.objects.filter(owner=request.user, deleted=False)
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)
    
class WorkspaceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=WorkspaceSerializer, responses=WorkspaceSerializer)
    def put(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user, deleted=False)
        except Workspace.DoesNotExist:
            return Response(
                { 'message': 'Workspace not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkspaceSerializer(workspace, data=request.data, partial=True)

        if serializer.is_valid():
            updated_workspace = serializer.save()
            return Response(
                WorkspaceSerializer(updated_workspace).data, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(request=WorkspaceSerializer, responses=WorkspaceSerializer)
    def delete(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user, deleted=False)
        except Workspace.DoesNotExist:
            return Response(
                { 'message': 'Workspace not found' },
                status=status.HTTP_404_NOT_FOUND
            )
        
        workspace.deleted = True
        workspace.deleted_at = timezone.now()
        workspace.save()
        
        return Response(
            { 'message': 'Workspace deleted successfully' },
            status=status.HTTP_204_NO_CONTENT
        )