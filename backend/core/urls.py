from django.urls import path
from .views import DemoTokenView, UserMeView

urlpatterns = [
    path('demo-token/', DemoTokenView.as_view(), name='demo-token'),
    path('me/', UserMeView.as_view(), name='user-me'),
]
