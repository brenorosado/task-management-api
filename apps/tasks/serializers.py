from rest_framework import serializers
from apps.tasks.models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'status', 'project', 'assigned_to', 'blocked_by', 'created_at', 'created_by', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    def create(self, validated_data):
        assigned_to = validated_data.pop('assigned_to', [])
        blocked_by = validated_data.pop('blocked_by', [])
        task = Task.objects.create(**validated_data)
        task.assigned_to.set(assigned_to)
        task.blocked_by.set(blocked_by)
        return task

    def update(self, instance, validated_data):
        if 'assigned_to' in validated_data:
            instance.assigned_to.set(validated_data.pop('assigned_to'))
        if 'blocked_by' in validated_data:
            instance.blocked_by.set(validated_data.pop('blocked_by'))
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.updated_by = validated_data.get('updated_by', instance.updated_by)
        instance.save()
        return instance