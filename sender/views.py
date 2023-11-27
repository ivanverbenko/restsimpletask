import json

from django.db.models import Q
from django.views import View
from django.http import JsonResponse
import requests
from firsttask.models import Dispatch
from django.views.decorators.csrf import csrf_protect



class BaseDispatchView(View):
    def __init__(self, url, fields_to_send):
        self.url = url
        initial_fields = ['id', 'broker_id', 'estate_id']
        self.fields_to_send = initial_fields + fields_to_send
        self.count_objects_to_send = 5 #количество записей, которое мы будем отсылать
        self.type = ''

    def send_data(self, data_to_send):
        try:
            response = requests.post(self.url, json=data_to_send)
            response_str = response.content.decode('utf-8')
            response_json = json.loads(response_str)
            if response.status_code == 200 and response_json['result']=='ok':
                return JsonResponse({'message': 'Dispatch sent successfully'})
            else:
                return JsonResponse({'message': 'Failed to send dispatch'}, status=500)
        except requests.exceptions.RequestException as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)

    def get(self, request):
        dispatch_objects = Dispatch.objects.filter(Q(sent=False) & Q(type=self.type)).order_by('id') \
            [:self.count_objects_to_send]
        if dispatch_objects:
            data_to_send_list = []
            for dispatch_object in dispatch_objects:
                data_to_send = {}
                for field in self.fields_to_send:
                    if hasattr(dispatch_object, field):
                        data_to_send[field] = getattr(dispatch_object, field)
                data_to_send_list.append(data_to_send)
            #POST-запрос с данными всех объектов
            response = self.send_data({"data":data_to_send_list})
            if response.status_code == 200:
                #обновление статуса
                for obj in dispatch_objects:
                    obj.sent = True
                # объекты в список для обновления
                objects_to_update = list(dispatch_objects)
                # массовое обновление
                Dispatch.objects.bulk_update(objects_to_update, ['sent'])
                return JsonResponse({"data":data_to_send_list})
            else:
                return JsonResponse({'message': 'Failed to send dispatch for all objects'}, status=500)
        else:
            return JsonResponse({'message': 'No data to send'}, status=400)


class EmailDispatchView(BaseDispatchView):
    def __init__(self):
        url = 'http://127.0.0.1:5000/echo'
        fields_to_send = ['email', 'name', 'message']
        super().__init__(url, fields_to_send)
        self.type = 'email'

class SMSDispatchView(BaseDispatchView):
    def __init__(self):
        url = 'http://127.0.0.1:5000/echo'
        fields_to_send = ['phone', 'name', 'message']
        super().__init__(url, fields_to_send)
        self.type = 'phone'