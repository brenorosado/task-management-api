from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.workspaces.models import Workspace
from apps.workspaces.serializers import WorkspaceSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination

class WorkspaceView(APIView):

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
    
    @extend_schema(
        responses=WorkspaceSerializer(many=True),
        parameters=[
            OpenApiParameter(name='page', type=int, required=False, default=1),
            OpenApiParameter(name='page_size', type=int, required=False, default=10)
        ]
    )
    def get(self, request):
        workspaces = Workspace.objects.filter(owner=request.user, deleted=False).order_by('-created_at')
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(workspaces, request)
        serializer = WorkspaceSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class WorkspaceDetailView(APIView):

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
            status=status.HTTP_200_OK
        )