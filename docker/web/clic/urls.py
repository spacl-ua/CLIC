from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
	path('', views.home, name='home'),
	path('signup/', views.signup, name='signup'),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path('logs/<task>/<phase>/<team>/<container>/', views.logs),
	path('submission/<task>/<phase>/<team>/', views.submission),
]
