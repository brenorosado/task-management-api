from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.projects.models import Project, ProjectMember
from apps.projects.serializers import ProjectSerializer
from apps.workspaces.models import Workspace
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from apps.users.models import User

class ProjectView(APIView):

    @extend_schema(request=ProjectSerializer, responses=ProjectSerializer)
    def post(self, request):
        serializer = ProjectSerializer(data=request.data)

        if serializer.is_valid():
            workspace_id = serializer.validated_data['workspace'].id
            try:
                Workspace.objects.get(id=workspace_id, owner=request.user, deleted=False)
            except Workspace.DoesNotExist:
                return Response(
                    { 'message': 'Workspace not found' },
                    status=status.HTTP_404_NOT_FOUND
                )

            project = serializer.save()
            return Response(
                ProjectSerializer(project).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectDetailView(APIView):
    @extend_schema(request=ProjectSerializer, responses=ProjectSerializer)
    def get(self, request, project_id):
        project = Project.objects.filter(
            Q(workspace__owner=request.user) | Q(memberships__user=request.user),
            id=project_id, workspace__deleted=False, deleted=False
        ).distinct().first()

        if not project:
            return Response({'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(request=ProjectSerializer, responses=ProjectSerializer)
    def put(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, workspace__owner=request.user, workspace__deleted=False, deleted=False)
        except Project.DoesNotExist:
            return Response(
                { 'message': 'Project not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectSerializer(project, data=request.data, partial=True)

        if serializer.is_valid():
            updated_project = serializer.save()
            return Response(
                ProjectSerializer(updated_project).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(request=ProjectSerializer, responses=ProjectSerializer)
    def delete(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, workspace__owner=request.user, workspace__deleted=False, deleted=False)
        except Project.DoesNotExist:
            return Response(
                { 'message': 'Project not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        project.deleted = True
        project.deleted_at = timezone.now()
        project.save()

        return Response(
            { 'message': 'Project deleted successfully' },
            status=status.HTTP_200_OK
        )

class ProjectMembersView(APIView):

    @extend_schema(request=ProjectSerializer, responses=ProjectSerializer)
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, workspace__owner=request.user, workspace__deleted=False, deleted=False)
        except Project.DoesNotExist:
            return Response(
                { 'message': 'Project not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        member_ids = request.data.get('member_ids', [])
        ProjectMember.objects.filter(project=project).delete()
        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id)
                ProjectMember.objects.get_or_create(project=project, user=user)
            except User.DoesNotExist:
                pass

        return Response(
            { 'message': 'Project members updated successfully' },
            status=status.HTTP_200_OK
        )

class ProjectsByWorkspaceView(APIView):
    @extend_schema(
        responses=ProjectSerializer(many=True),
        parameters=[
            OpenApiParameter(name='page', type=int, required=False, default=1),
            OpenApiParameter(name='page_size', type=int, required=False, default=10)
        ]
    )
    def get(self, request, workspace_id):
        try:
            Workspace.objects.get(id=workspace_id, owner=request.user, deleted=False)
        except Workspace.DoesNotExist:
            return Response(
                { 'message': 'Workspace not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        projects = Project.objects.filter(workspace_id=workspace_id, deleted=False).order_by('-created_at')
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(projects, request)
        serializer = ProjectSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)