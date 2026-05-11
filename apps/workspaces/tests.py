from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.workspaces.models import Workspace


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
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)

    def url(self, workspace_id):
        return f'/api/workspaces/{workspace_id}'

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

    def test_update_workspace_unauthenticated(self):
        response = self.client.put(self.url(self.workspace.id), {'name': 'X'})
        self.assertEqual(response.status_code, 401)

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

    def test_delete_workspace_unauthenticated(self):
        response = self.client.delete(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 401)
