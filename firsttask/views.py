from string import Template

from django.db.models import Q
from jinja2 import Template
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from firsttask.models import Dispatch
from firsttask.serializers import DataSerializer


class ScheduleCreateView(APIView):
    def post(self, request):
        serializer = DataSerializer(data=request.data)
        print(serializer.is_valid())
        if serializer.is_valid():
            name = serializer.validated_data['name']
            message_template = serializer.validated_data['message_template'].replace('[', '{{').replace(']', '}}')
            scopes = serializer.validated_data['scopes']
            dispatches_to_create = []
            sent_messages = []  # To track sent messages
            sucsessfull_scopes = []
            failed_scopes = []
            for scope in scopes:
                type = serializer.validated_data['type']
                contact = scope['retail']['contact']['email'] if type == "email" \
                    else scope['retail']['contact']['phone']

                # Check if the same estate.id and contact have been sent before
                filter_query = Q(estate_id=scope['estate']['id']) & (Q(email=contact) | Q(phone=contact))
                existing_sent_message = Dispatch.objects.filter(filter_query).first()

                if existing_sent_message:
                    error_message = f"Ошибка {type}: {scope['estate']['id']}"
                    failed_scopes.append({
                        'scope': scope,
                        'errors': error_message,
                        'entityId': existing_sent_message.id
                    })
                else:
                    template = Template(message_template)
                    formatted_message = template.render(**scope)
                    print(scope)
                    dispatch_dict = {
                        'name': name,
                        'message': formatted_message,
                        'retail_id': scope['retail']['personid'],
                        'broker_id': serializer.validated_data['broker']['id'],
                        'estate_id': scope['estate']['id'],
                        'type': type,
                        'email': contact if type == "email" else None,
                        'phone': contact if type == "WhatsApp" else None
                    }
                    dispatches_to_create.append(dispatch_dict)
                    sucsessfull_scopes.append(scope)
            dispatch_objects_to_create = [Dispatch(**dispatch_dict) for dispatch_dict in dispatches_to_create]
            Dispatch.objects.bulk_create(dispatch_objects_to_create)
            return Response({"result":{"scopes":sucsessfull_scopes+failed_scopes+serializer.validated_data['scopes_erros']}}\
                            , status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
