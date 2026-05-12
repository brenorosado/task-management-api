from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer
from apps.projects.models import Project
from apps.workspaces.models import Workspace
from django.db.models import Q
from django.utils import timezone
from apps.users.models import User


class TaskPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


def has_cycle(task_id, blocker_ids):
    visited = set()
    queue = list(blocker_ids)
    while queue:
        current_id = str(queue.pop(0))
        if current_id == str(task_id):
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        current = Task.objects.filter(id=current_id).first()
        if current:
            queue.extend(current.blocked_by.values_list('id', flat=True))
    return False


def validate_task_relations(request, project, task=None):
    blocked_by = request.data.get('blocked_by', [])
    for task_id in blocked_by:
        try:
            Task.objects.get(id=task_id, project=project)
        except Task.DoesNotExist:
            return Response(
                {'message': f'Blocked task with id {task_id} not found in the project'},
                status=status.HTTP_404_NOT_FOUND
            )

    if task and blocked_by and has_cycle(task.id, blocked_by):
        return Response(
            {'message': 'Circular dependency detected in blocked_by'},
            status=status.HTTP_400_BAD_REQUEST
        )

    assigned_to = request.data.get('assigned_to', [])
    for assigned_to_id in assigned_to:
        try:
            user = User.objects.get(id=assigned_to_id)
            if not project.memberships.filter(user=user).exists():
                return Response(
                    {'message': f'User {assigned_to_id} is not a member of the project'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'message': f'Assigned user with id {assigned_to_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    return None


def apply_task_filters(tasks, request):
    status_filter = request.query_params.get('status')
    if status_filter:
        valid_statuses = [s[0] for s in Task.Status.choices]
        if status_filter not in valid_statuses:
            return None, Response(
                {'message': f'Invalid status. Valid values are: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        tasks = tasks.filter(status=status_filter)

    assigned_to = request.query_params.get('assigned_to')
    if assigned_to:
        tasks = tasks.filter(assigned_to__id=assigned_to)

    blocked_by = request.query_params.get('blocked_by')
    if blocked_by:
        tasks = tasks.filter(blocked_by__id=blocked_by)

    return tasks, None


class TaskView(APIView):

    @extend_schema(request=TaskSerializer, responses=TaskSerializer)
    def post(self, request):
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            project_id = serializer.validated_data['project'].id

            project = Project.objects.filter(
                Q(workspace__owner=request.user) | Q(memberships__user=request.user),
                id=project_id, workspace__deleted=False, deleted=False
            ).distinct().first()

            if not project:
                return Response(
                    { 'message': 'Project not found' },
                    status=status.HTTP_404_NOT_FOUND
                )

            error = validate_task_relations(request, project)
            if error:
                return error

            task = serializer.save(created_by=request.user)
            return Response(
                TaskSerializer(task).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class TaskDetailView(APIView):

    @extend_schema(request=TaskSerializer, responses=TaskSerializer)
    def get(self, request, task_id):
        task = Task.objects.filter(
            Q(project__workspace__owner=request.user) | Q(project__memberships__user=request.user),
            id=task_id, project__workspace__deleted=False, project__deleted=False, deleted=False
        ).distinct().first()

        if not task:
            return Response({'message': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(request=TaskSerializer, responses=TaskSerializer)
    def put(self, request, task_id):
        task = Task.objects.filter(
            Q(project__workspace__owner=request.user) | Q(project__memberships__user=request.user),
            id=task_id, project__workspace__deleted=False, project__deleted=False, deleted=False
        ).distinct().first()

        if not task:
            return Response({'message': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        project = task.project

        error = validate_task_relations(request, project, task=task)
        if error:
            return error

        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            updated_task = serializer.save(updated_by=request.user)
            return Response(
                TaskSerializer(updated_task).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: None})
    def delete(self, request, task_id):
        task = Task.objects.filter(
            Q(project__workspace__owner=request.user) | Q(project__memberships__user=request.user),
            id=task_id, project__workspace__deleted=False, project__deleted=False, deleted=False
        ).distinct().first()

        if not task:
            return Response({'message': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        task.deleted = True
        task.deleted_at = timezone.now()
        task.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeletedTaskView(APIView):

    @extend_schema(
        responses=TaskSerializer(many=True),
        parameters=[
            OpenApiParameter(name='page', type=int, required=False, default=1),
            OpenApiParameter(name='page_size', type=int, required=False, default=10),
        ]
    )
    def get(self, request, project_id):
        project = Project.objects.filter(
            id=project_id, workspace__owner=request.user, workspace__deleted=False, deleted=False
        ).first()

        if not project:
            return Response({'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks = Task.objects.filter(
            project=project, deleted=True
        ).order_by('-deleted_at')

        paginator = TaskPagination()
        page = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TaskReactivateView(APIView):

    @extend_schema(responses=TaskSerializer)
    def post(self, request, task_id):
        task = Task.objects.filter(
            id=task_id, project__workspace__owner=request.user,
            project__workspace__deleted=False, project__deleted=False, deleted=True
        ).first()

        if not task:
            return Response({'message': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        task.deleted = False
        task.deleted_at = None
        task.save()

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )


class TasksByProjectView(APIView):

    @extend_schema(
        responses=TaskSerializer(many=True),
        parameters=[
            OpenApiParameter(name='page', type=int, required=False, default=1),
            OpenApiParameter(name='page_size', type=int, required=False, default=10),
            OpenApiParameter(name='status', type=str, required=False),
            OpenApiParameter(name='assigned_to', type=str, required=False),
            OpenApiParameter(name='blocked_by', type=str, required=False),
        ]
    )
    def get(self, request, project_id):
        project = Project.objects.filter(
            Q(workspace__owner=request.user) | Q(memberships__user=request.user),
            id=project_id, workspace__deleted=False, deleted=False
        ).distinct().first()

        if not project:
            return Response({'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks, error = apply_task_filters(
            Task.objects.filter(project=project, deleted=False),
            request
        )
        if error:
            return error

        paginator = TaskPagination()
        page = paginator.paginate_queryset(tasks.order_by('-created_at').distinct(), request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TasksByWorkspaceView(APIView):

    @extend_schema(
        responses=TaskSerializer(many=True),
        parameters=[
            OpenApiParameter(name='page', type=int, required=False, default=1),
            OpenApiParameter(name='page_size', type=int, required=False, default=10),
            OpenApiParameter(name='status', type=str, required=False),
            OpenApiParameter(name='assigned_to', type=str, required=False),
            OpenApiParameter(name='blocked_by', type=str, required=False),
        ]
    )
    def get(self, request, workspace_id):
        workspace = Workspace.objects.filter(
            Q(owner=request.user) | Q(projects__memberships__user=request.user),
            id=workspace_id, deleted=False
        ).distinct().first()

        if not workspace:
            return Response({'message': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks, error = apply_task_filters(
            Task.objects.filter(
                project__workspace=workspace, project__deleted=False, deleted=False
            ),
            request
        )
        if error:
            return error

        paginator = TaskPagination()
        page = paginator.paginate_queryset(tasks.order_by('-created_at').distinct(), request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
