import aiohttp
from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import asyncio
import httpx
from firsttask.models import Dispatch


class AsyncDataSendView(APIView):
    async def get(self, request):
        url = "https://api.example.com/data"  # Замените на ваш URL
        return JsonResponse({"data": "data"})

    # async def async_get(self, request):
    #     data_to_send = await self.get_data_from_db()
    #     await self.send_data_to_external_service(data_to_send)
    #
    #     response = Response({"message": "Асинхронная отправка начата"})
    #     return response

    # async def get_data_from_db(self):
    #     # Извлекаем все записи из базы данных
    #     queryset = Dispatch.objects.all()
    #
    #     # Преобразуем записи в список словарей
    #     data_list = []
    #     for item in queryset:
    #         data_list.append({
    #             "name": item.name,
    #             "message": item.message,
    #             "retail_id": item.retail_id,
    #             "estate_id": item.estate_id,
    #             "broker_id": item.broker_id,
    #             "type": item.type,
    #             "phone": item.phone,
    #             "email": item.email,
    #             "sent": item.sent,
    #         })
    #
    #     return data_list
    #
    # async def send_data_to_external_service(self, data):
    #     async with aiohttp.ClientSession() as session:
    #         url = "http://localhost:8080"
    #         headers = {"Content-Type": "application/json"}
    #
    #         for item in data:
    #             print(f"Отправка данных: {item}")
    #             await asyncio.sleep(2)  # Затычка для асинхронной операции
    #             print(f"Данные {item} успешно отправлены на затычковый сервер")