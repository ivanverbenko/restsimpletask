
from rest_framework import serializers

class EstateSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=200)
    sq = serializers.IntegerField()

class ScopeSerializer(serializers.Serializer):
    retail = serializers.CharField()
    estate = EstateSerializer()

class DispatchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    scopes = ScopeSerializer(many=True)
    message_template = serializers.CharField(max_length=200)