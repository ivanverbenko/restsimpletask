import json
from django.db.models import Q
from django.http import JsonResponse
import requests
from dataHandler.models import Dispatch
from distribution import settings
from abc import ABC, abstractmethod


class BaseDispatchView(ABC):
    """Базовый класс, от которого будет наследоваться дальнейшие рассылки на API-сервисы"""
    def __init__(self, fields_to_send,type):
        self.fields_to_send = fields_to_send
        self.type = type

    def response_answer(self, message, status):
        return JsonResponse({'message': message}, status=status)

    @abstractmethod
    def send_data_to_api(self, data_to_send):
        pass

    @property
    @abstractmethod
    def url(self):
        pass

    def update_status(self, dispatch_objects):
        """Обновление статуса отправки через bulk_update, так как update  не поддерживает обновление полей моделей,
         которые были выбраны с помощью сложных запросов, таких как условия с использованием Q"""
        for obj in dispatch_objects:
            obj.sent = True
        objects_to_update = list(dispatch_objects)
        Dispatch.objects.bulk_update(objects_to_update, ['sent'])


    def send(self):
        dispatch_objects = Dispatch.objects.filter(Q(sent=False) & Q(type=self.type)).order_by('id') \
            [:settings.COUNTS_OBJECTS_TO_SEND]
        if not dispatch_objects:
            return self.response_answer(message='No data to send', status=500)
        data_to_send_list = list(dispatch_objects.values_list(*self.fields_to_send))
        response = self.send_data_to_api({"data": data_to_send_list})
        if response.status_code != 200:
            return self.response_answer(message='Failed to send dispatch for all objects', status=500)
        self.update_status(dispatch_objects)
        return self.response_answer(message=data_to_send_list, status=200)

class LocalhostDispatchView(BaseDispatchView):
    @property
    def url(self):
        return "http://127.0.0.1:5000/echo"
    def send_data_to_api(self, data_to_send):
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

    def response_answer(self, message, status):
        return JsonResponse({'message': message}, status=status)
