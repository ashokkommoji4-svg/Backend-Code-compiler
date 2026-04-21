from django.urls import path
from apps.compiler.api.views import CodeExecutionView

urlpatterns = [
    path('execute/', CodeExecutionView.as_view(), name='execute-code'),
]
