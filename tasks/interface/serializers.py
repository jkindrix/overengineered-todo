"""DRF serializers for request validation.

Responses are rendered by presenters (plain dicts), so these serializers focus
on *input* validation. The domain enums are the single source of truth for the
allowed choices.
"""

from __future__ import annotations

from rest_framework import serializers

from tasks.domain.value_objects import Priority, TaskStatus


class CreateTaskSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=5000
    )
    priority = serializers.ChoiceField(
        choices=[p.name for p in Priority], required=False, default="NORMAL"
    )


class EditTaskSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=5000
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Provide at least one of: title, description."
            )
        return attrs


class ChangePrioritySerializer(serializers.Serializer):
    priority = serializers.ChoiceField(choices=[p.name for p in Priority])


class TransitionSerializer(serializers.Serializer):
    target_status = serializers.ChoiceField(choices=[s.value for s in TaskStatus])
