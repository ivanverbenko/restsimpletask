import json
from django.db.models import Q
from django.http import JsonResponse
import requests
from firsttask.models import Dispatch
from distribution import settings


class BaseDispatchView():
    def __init__(self, url, fields_to_send,type):
        self.url = url
        self.fields_to_send = fields_to_send
        self.count_objects_to_send = settings.COUNTS_OBJECTS_TO_SEND
        self.type = type

    def response_answer(self, message, status):
        return JsonResponse({'message': message}, status=status)

    def send_data(self, data_to_send):
        "Отправка данных на указанный URL-адрес"
        try:
            response = requests.post(self.url, json=data_to_send)
            response_str = response.content.decode('utf-8')
            response_json = json.loads(response_str)
            if response.status_code == 200 and response_json['result'] == 'ok':
                return self.response_answer(message='Dispatch sent successfully', status=200)
            else:
                return self.response_answer(message='Failed to send dispatch', status=500)
        except requests.exceptions.RequestException as e:
            return self.response_answer(message=f'Error: {str(e)}', status=500)

    def update_data(self, dispatch_objects):
        "Обновление статуса отправки в базе данных"
        for obj in dispatch_objects:
            obj.sent = True
        objects_to_update = list(dispatch_objects)
        Dispatch.objects.bulk_update(objects_to_update, ['sent'])

    def send(self):
        dispatch_objects = Dispatch.objects.filter(Q(sent=False) & Q(type=self.type)).order_by('id') \
            [:self.count_objects_to_send]
        if dispatch_objects:
            data_to_send_list = list(dispatch_objects.values_list(*self.fields_to_send))
            response = self.send_data({"data": data_to_send_list})
            if response.status_code == 200:
                self.update_data(dispatch_objects)
                return self.response_answer(message=data_to_send_list, status=200)
            else:
                return self.response_answer(message='Failed to send dispatch for all objects', status=500)



