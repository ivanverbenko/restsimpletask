from string import Template

from django.db.models import Q
from jinja2 import Template
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dataHandler.models import Dispatch
from dataHandler.serializers import DataSerializer


class ScheduleCreateView(APIView):
    def post(self, request):
        serializer = DataSerializer(data=request.data)
        if serializer.is_valid():
            dispatch_serializer = DataSerializer(data=serializer.validated_data)
            if dispatch_serializer.is_valid():
                failed_scopes, sucsessful_scopes = dispatch_serializer.save()
                return Response({
                    "result": {
                        "scopes": sucsessful_scopes + serializer.validated_data['scopes_erros'] + failed_scopes
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(dispatch_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
