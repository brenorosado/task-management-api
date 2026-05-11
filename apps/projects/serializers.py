from rest_framework import serializers
from apps.projects.models import Project, ProjectMember
from apps.users.serializers import UserSerializer

class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['user', 'created_at']

class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMemberSerializer(source='memberships', many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'workspace', 'members', 'created_at', 'updated_at', 'deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted', 'deleted_at', 'members']

    def create(self, validated_data):
        return Project.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance