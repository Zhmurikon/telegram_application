from django.urls import path
from .views import LeadCreateView, SubscribeView

urlpatterns = [
    path('leads/', LeadCreateView.as_view(), name='lead-create'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]