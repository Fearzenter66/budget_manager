from django.urls import path

from core.api.views import HealthCheckView

app_name = 'api'

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
]
