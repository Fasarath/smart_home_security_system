from rest_framework import serializers
from .models import AuthLog

class AuthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthLog
        fields = ['id', 'timestamp', 'authenticated']