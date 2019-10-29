from django.urls import path

from . import views

urlpatterns = [
	path('status/<pk>/<status>/', views.update),
]
