from string import Template

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from firsttask.models import Dispatch
from firsttask.serializers import DispatchCreateSerializer


class ScheduleCreateView(APIView):
    def post(self, request):
        serializer = DispatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            message_template = serializer.validated_data['message_template'].replace('[','{').replace(']','}')
            scopes = serializer.validated_data['scopes']
            dispatches_to_create = []
            for scope in scopes:
                retail_name = scope['retail']
                estate_address = scope['estate']['address']
                square = scope['estate']['sq']
                message = message_template.format(retail_name=retail_name, estate_address=estate_address, estate_square=square)
                dispatches_to_create.append(Dispatch(name=name, message=message))
            Dispatch.objects.bulk_create(dispatches_to_create)
            return Response("Data saved successfully", status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)