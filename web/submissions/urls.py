from django.urls import path

from . import views

urlpatterns = [
	path('<pk>/status/', views.status),
	path('<pk>/metrics/', views.metrics),
	path('<pk>/decoding_time/', views.decoding_time),
]
