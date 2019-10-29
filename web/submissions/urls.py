from django.urls import path

from . import views

urlpatterns = [
	path('status/<pk>/<status>/', views.status),
	path('results/<pk>/', views.results),
]
