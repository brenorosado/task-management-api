from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.workspaces.models import Workspace
from apps.projects.models import Project, ProjectMember


class ProjectViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.url = '/api/projects'

    def test_create_project_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Project', 'workspace': self.workspace.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'My Project')

    def test_create_project_unauthenticated(self):
        response = self.client.post(self.url, {'name': 'My Project', 'workspace': self.workspace.id})
        self.assertEqual(response.status_code, 401)

    def test_create_project_missing_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'workspace': self.workspace.id})
        self.assertEqual(response.status_code, 400)

    def test_create_project_workspace_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'name': 'My Project', 'workspace': '00000000-0000-0000-0000-000000000000'})
        self.assertEqual(response.status_code, 400)

    def test_create_project_workspace_belongs_to_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self.url, {'name': 'My Project', 'workspace': self.workspace.id})
        self.assertEqual(response.status_code, 404)


class ProjectDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)
        ProjectMember.objects.create(project=self.project, user=self.member_user)

    def url(self, project_id):
        return f'/api/projects/{project_id}'

    # GET
    def test_get_project_as_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Project')

    def test_get_project_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'My Project')

    def test_get_project_returns_members_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['members']), 1)
        member = response.data['members'][0]['user']
        self.assertEqual(member['email'], 'member@example.com')
        self.assertEqual(member['name'], 'Member')
        self.assertNotIn('password', member)

    def test_get_project_returns_empty_members_when_none(self):
        project = Project.objects.create(name='No Members', workspace=self.workspace)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url(project.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['members'], [])

    def test_get_project_not_member(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)

    def test_get_project_unauthenticated(self):
        response = self.client.get(self.url(self.project.id))
        self.assertEqual(response.status_code, 401)

    # PUT
    def test_update_project_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url(self.project.id), {'name': 'Renamed'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Renamed')

    def test_update_project_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.put(self.url(self.project.id), {'name': 'Hacked'})
        self.assertEqual(response.status_code, 404)

    def test_update_project_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url('00000000-0000-0000-0000-000000000000'), {'name': 'X'})
        self.assertEqual(response.status_code, 404)

    def test_update_project_from_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.put(self.url(self.project.id), {'name': 'Hacked'})
        self.assertEqual(response.status_code, 404)

    def test_update_project_unauthenticated(self):
        response = self.client.put(self.url(self.project.id), {'name': 'X'})
        self.assertEqual(response.status_code, 401)

    # DELETE
    def test_delete_project_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url(self.project.id))
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertTrue(self.project.deleted)
        self.assertIsNotNone(self.project.deleted_at)

    def test_delete_project_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)

    def test_delete_project_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url('00000000-0000-0000-0000-000000000000'))
        self.assertEqual(response.status_code, 404)

    def test_delete_project_from_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)

    def test_delete_project_unauthenticated(self):
        response = self.client.delete(self.url(self.project.id))
        self.assertEqual(response.status_code, 401)

    def test_delete_already_deleted_project(self):
        self.client.force_authenticate(user=self.user)
        self.project.deleted = True
        self.project.save()
        response = self.client.delete(self.url(self.project.id))
        self.assertEqual(response.status_code, 404)


class ProjectMembersViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.member_user = User.objects.create_user('member@example.com', 'Member', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)
        self.project = Project.objects.create(name='My Project', workspace=self.workspace)

    def url(self, project_id):
        return f'/api/projects/{project_id}/members'

    def test_add_members_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url(self.project.id), {'member_ids': [str(self.member_user.id)]}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.member_user).exists())

    def test_add_members_replaces_existing(self):
        ProjectMember.objects.create(project=self.project, user=self.other_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url(self.project.id), {'member_ids': [str(self.member_user.id)]}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.member_user).exists())
        self.assertFalse(ProjectMember.objects.filter(project=self.project, user=self.other_user).exists())

    def test_add_members_empty_list_removes_all(self):
        ProjectMember.objects.create(project=self.project, user=self.member_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url(self.project.id), {'member_ids': []}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProjectMember.objects.filter(project=self.project).count(), 0)

    def test_add_members_not_owner(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self.url(self.project.id), {'member_ids': []}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_add_members_unauthenticated(self):
        response = self.client.post(self.url(self.project.id), {'member_ids': []}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_add_members_project_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url('00000000-0000-0000-0000-000000000000'), {'member_ids': []}, format='json')
        self.assertEqual(response.status_code, 404)


class ProjectsByWorkspaceViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Xk9#mP2$qR7!')
        self.other_user = User.objects.create_user('jane@example.com', 'Jane', 'Xk9#mP2$qR7!')
        self.workspace = Workspace.objects.create(name='My Workspace', owner=self.user)

    def url(self, workspace_id):
        return f'/api/workspaces/{workspace_id}/projects'

    def test_list_projects_success(self):
        self.client.force_authenticate(user=self.user)
        Project.objects.create(name='Project A', workspace=self.workspace)
        Project.objects.create(name='Project B', workspace=self.workspace)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_list_projects_excludes_deleted(self):
        self.client.force_authenticate(user=self.user)
        Project.objects.create(name='Active', workspace=self.workspace)
        Project.objects.create(name='Deleted', workspace=self.workspace, deleted=True)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active')

    def test_list_projects_workspace_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url('00000000-0000-0000-0000-000000000000'))
        self.assertEqual(response.status_code, 404)

    def test_list_projects_workspace_belongs_to_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 404)

    def test_list_projects_unauthenticated(self):
        response = self.client.get(self.url(self.workspace.id))
        self.assertEqual(response.status_code, 401)
