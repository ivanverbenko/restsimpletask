from django.urls import path
from .views import EmailDispatchView, SMSDispatchView
urlpatterns = [
    path('send-email/', EmailDispatchView.as_view(), name='send_email'),
    path('send-sms/', SMSDispatchView.as_view(), name='send_sms'),
]