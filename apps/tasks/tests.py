from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.workspaces.models import Workspace
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('owner@example.com', 'Owner', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('other@example.com', 'Other', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.url = '/api/tasks'

    def test_create_task_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Task', 'project': self.project.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'My Task')
        self.assertEqual(response.data['status'], 'todo')

    def test_create_task_sets_created_by(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Task', 'project': self.project.id})
        self.assertEqual(response.status_code, 201)
        task = Task.objects.get(id=response.data['id'])
        self.assertEqual(task.created_by, self.user)

    def test_create_task_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.post(self.url, {'name': 'My Task', 'project': self.project.id})
        self.assertEqual(response.status_code, 201)

    def test_create_task_unauthenticated(self):
        response = self.client.post(self.url, {'name': 'My Task', 'project': self.project.id})
        self.assertEqual(response.status_code, 401)

    def test_create_task_invalid_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Task', 'project': '00000000-0000-0000-0000-000000000000'})
        self.assertEqual(response.status_code, 400)

    def test_create_task_non_member_project(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self.url, {'name': 'My Task', 'project': self.project.id})
        self.assertEqual(response.status_code, 404)

    def test_create_task_missing_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'project': self.project.id})
        self.assertEqual(response.status_code, 400)

    def test_create_task_with_assigned_to_non_member(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            'name': 'My Task',
            'project': self.project.id,
            'assigned_to': [self.other_user.id]
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_task_with_assigned_to_member(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            'name': 'My Task',
            'project': self.project.id,
            'assigned_to': [self.member_user.id]
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_task_with_blocked_by_different_project(self):
        other_project = Project.objects.create(name='Other Project', workspace=self.workspace)
        blocking_task = Task.objects.create(name='Blocker', project=other_project, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            'name': 'My Task',
            'project': self.project.id,
            'blocked_by': [blocking_task.id]
        }, format='json')
        self.assertEqual(response.status_code, 404)

    def test_create_task_with_blocked_by_same_project(self):
        blocking_task = Task.objects.create(name='Blocker', project=self.project, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            'name': 'My Task',
            'project': self.project.id,
            'blocked_by': [blocking_task.id]
        }, format='json')
        self.assertEqual(response.status_code, 201)


class TaskDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('owner@example.com', 'Owner', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('other@example.com', 'Other', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.task = Task.objects.create(name='My Task', project=self.project, created_by=self.user)

    def url(self, task_id):
        return f'/api/tasks/{task_id}'

    def test_get_task_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.task.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Task')

    def test_get_task_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.task.id))
        self.assertEqual(response.status_code, 200)

    def test_get_task_unauthenticated(self):
        response = self.client.get(self.url(self.task.id))
        self.assertEqual(response.status_code, 401)

    def test_get_task_non_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url(self.task.id))
        self.assertEqual(response.status_code, 404)

    def test_get_deleted_task_returns_404(self):
        self.task.deleted = True
        self.task.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.task.id))
        self.assertEqual(response.status_code, 404)

    def test_update_task_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.task.id), {'name': 'Updated Task', 'status': 'in_progress'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Updated Task')
        self.assertEqual(response.data['status'], 'in_progress')

    def test_update_task_partial(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.task.id), {'status': 'done'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'done')
        self.assertEqual(response.data['name'], 'My Task')

    def test_update_task_sets_updated_by(self):
        self.client.force_authenticate(user=self.user)
        self.client.put(self.url(self.task.id), {'status': 'done'})
        self.task.refresh_from_db()
        self.assertEqual(self.task.updated_by, self.user)

    def test_update_task_unauthenticated(self):
        response = self.client.put(self.url(self.task.id), {'name': 'Updated'})
        self.assertEqual(response.status_code, 401)

    def test_update_task_non_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.put(self.url(self.task.id), {'name': 'Updated'})
        self.assertEqual(response.status_code, 404)

    def test_update_deleted_task(self):
        self.task.deleted = True
        self.task.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.task.id), {'name': 'Updated'})
        self.assertEqual(response.status_code, 404)

    def test_update_task_with_assigned_to_non_member(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.task.id), {'assigned_to': [self.other_user.id]}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_delete_task_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url(self.task.id))
        self.assertEqual(response.status_code, 204)

    def test_delete_task_sets_deleted_fields(self):
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.url(self.task.id))
        self.task.refresh_from_db()
        self.assertTrue(self.task.deleted)
        self.assertIsNotNone(self.task.deleted_at)

    def test_delete_task_unauthenticated(self):
        response = self.client.delete(self.url(self.task.id))
        self.assertEqual(response.status_code, 401)

    def test_delete_task_non_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url(self.task.id))
        self.assertEqual(response.status_code, 404)

    def test_delete_already_deleted_task(self):
        self.task.deleted = True
        self.task.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url(self.task.id))
        self.assertEqual(response.status_code, 404)


class TasksByProjectViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('owner@example.com', 'Owner', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('other@example.com', 'Other', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.task = Task.objects.create(name='My Task', project=self.project, created_by=self.user)

    def url(self, project_id):
        return f'/api/projects/{project_id}/tasks'

    def test_get_tasks_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_get_tasks_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)

    def test_get_tasks_unauthenticated(self):
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 401)

    def test_get_tasks_non_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)

    def test_get_tasks_invalid_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url('00000000-0000-0000-0000-000000000000'))
        self.assertEqual(response.status_code, 404)

    def test_get_tasks_excludes_deleted(self):
        self.task.deleted = True
        self.task.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.data['count'], 0)

    def test_get_tasks_filter_by_status(self):
        Task.objects.create(name='Done Task', project=self.project, created_by=self.user, status='done')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id), {'status': 'done'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Done Task')

    def test_get_tasks_filter_by_assigned_to(self):
        assigned_task = Task.objects.create(name='Assigned Task', project=self.project, created_by=self.user)
        assigned_task.assigned_to.set([self.member_user])
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id), {'assigned_to': self.member_user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Assigned Task')

    def test_get_tasks_filter_by_blocked_by(self):
        blocking_task = Task.objects.create(name='Blocker', project=self.project, created_by=self.user)
        blocked_task = Task.objects.create(name='Blocked Task', project=self.project, created_by=self.user)
        blocked_task.blocked_by.set([blocking_task])
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id), {'blocked_by': blocking_task.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Blocked Task')

    def test_get_tasks_paginated(self):
        for i in range(2, 12):
            Task.objects.create(name=f'Task {i}', project=self.project, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id), {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])


class DeletedTaskViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('owner@example.com', 'Owner', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.task = Task.objects.create(name='My Task', project=self.project, created_by=self.user, deleted=True)

    def url(self, project_id):
        return f'/api/projects/{project_id}/deleted_tasks'

    def test_get_deleted_tasks_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'My Task')

    def test_get_deleted_tasks_excludes_active(self):
        Task.objects.create(name='Active Task', project=self.project, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.data['count'], 1)

    def test_get_deleted_tasks_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)

    def test_get_deleted_tasks_unauthenticated(self):
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 401)

    def test_get_deleted_tasks_invalid_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url('00000000-0000-0000-0000-000000000000'))
        self.assertEqual(response.status_code, 404)

    def test_get_deleted_tasks_paginated(self):
        for i in range(2, 12):
            Task.objects.create(name=f'Task {i}', project=self.project, created_by=self.user, deleted=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id), {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])


class TaskReactivateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('owner@example.com', 'Owner', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.task = Task.objects.create(name='My Task', project=self.project, created_by=self.user, deleted=True)

    def url(self, task_id):
        return f'/api/tasks/{task_id}/reactivate'

    def test_reactivate_task_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url(self.task.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Task')

    def test_reactivate_task_clears_deleted_fields(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url(self.task.id))
        self.task.refresh_from_db()
        self.assertFalse(self.task.deleted)
        self.assertIsNone(self.task.deleted_at)

    def test_reactivate_task_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.post(self.url(self.task.id))
        self.assertEqual(response.status_code, 404)

    def test_reactivate_task_unauthenticated(self):
        response = self.client.post(self.url(self.task.id))
        self.assertEqual(response.status_code, 401)

    def test_reactivate_non_deleted_task(self):
        active_task = Task.objects.create(name='Active', project=self.project, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url(active_task.id))
        self.assertEqual(response.status_code, 404)
