from rest_framework import serializers

from ..models import Organization


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = "__all__"


class OrganizationCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        exclude = ('id', 'is_active',)
