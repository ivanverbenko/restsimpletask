from string import Template

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from firsttask.models import Dispatch
from firsttask.serializers import DataSerializer

from jinja2 import Template

class ScheduleCreateView(APIView):
    def post(self, request):
        serializer = DataSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            message_template = serializer.validated_data['message_template'].replace('[','{{').replace(']','}}')
            scopes = serializer.validated_data['scopes']
            dispatches_to_create = []
            for scope in scopes:
                template = Template(message_template)
                formatted_message = template.render(**scope)
                dispatches_to_create.append(Dispatch(name=name, message=formatted_message))
            Dispatch.objects.bulk_create(dispatches_to_create)
            return Response("Data saved successfully", status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)