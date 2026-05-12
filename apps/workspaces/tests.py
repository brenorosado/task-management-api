from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.workspaces.models import Workspace
from apps.projects.models import Project, ProjectMember


class WorkspaceViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.url = '/api/workspaces'

    def test_create_workspace_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Workspace'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'My Workspace')
        self.assertEqual(response.data['owner'], self.user.id)

    def test_create_workspace_unauthenticated(self):
        response = self.client.post(self.url, {'name': 'My Workspace'})
        self.assertEqual(response.status_code, 401)

    def test_create_workspace_missing_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_list_workspaces_only_returns_own(self):
        self.client.force_authenticate(user=self.user)
        Workspace.objects.create(name='Mine', owner=self.user)
        Workspace.objects.create(name='Not Mine', owner=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Mine')

    def test_list_workspaces_includes_member_workspaces(self):
        other_workspace = Workspace.objects.create(name='Other Workspace', owner=self.other_user)
        project = Project.objects.create(name='A Project', workspace=other_workspace)
        ProjectMember.objects.create(project=project, user=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        names = [w['name'] for w in response.data['results']]
        self.assertIn('Other Workspace', names)

    def test_list_workspaces_no_duplicates_with_multiple_memberships(self):
        other_workspace = Workspace.objects.create(name='Other Workspace', owner=self.other_user)
        project_a = Project.objects.create(name='Project A', workspace=other_workspace)
        project_b = Project.objects.create(name='Project B', workspace=other_workspace)
        ProjectMember.objects.create(project=project_a, user=self.user)
        ProjectMember.objects.create(project=project_b, user=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_list_workspaces_excludes_deleted(self):
        self.client.force_authenticate(user=self.user)
        Workspace.objects.create(name='Active', owner=self.user)
        Workspace.objects.create(name='Deleted', owner=self.user, deleted=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active')

    def test_list_workspaces_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class WorkspaceDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)

    def url(self, workspace_id):
        return f'/api/workspaces/{workspace_id}'

    # GET
    def test_get_workspace_as_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Workspace')

    def test_get_workspace_as_project_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Workspace')

    def test_get_workspace_not_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 404)

    def test_get_workspace_unauthenticated(self):
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 401)

    # PUT
    def test_update_workspace_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.workspace.id), {'name': 'Renamed'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Renamed')

    def test_update_workspace_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url('00000000-0000-0000-0000-000000000000'), {'name': 'X'})
        self.assertEqual(response.status_code, 404)

    def test_update_workspace_from_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.put(self.url(self.workspace.id), {'name': 'Hacked'})
        self.assertEqual(response.status_code, 404)

    def test_update_workspace_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.put(self.url(self.workspace.id), {'name': 'Hacked'})
        self.assertEqual(response.status_code, 404)

    def test_update_workspace_unauthenticated(self):
        response = self.client.put(self.url(self.workspace.id), {'name': 'X'})
        self.assertEqual(response.status_code, 401)

    # DELETE
    def test_delete_workspace_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 204)
        self.workspace.refresh_from_db()
        self.assertTrue(self.workspace.deleted)
        self.assertIsNotNone(self.workspace.deleted_at)

    def test_delete_workspace_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url('00000000-0000-0000-0000-000000000000'))
        self.assertEqual(response.status_code, 404)

    def test_delete_workspace_from_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 404)

    def test_delete_workspace_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 404)

    def test_delete_workspace_unauthenticated(self):
        response = self.client.delete(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 401)
