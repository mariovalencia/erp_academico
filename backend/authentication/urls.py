from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('google/', views.google_login, name='google_login'),
]