from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from . import views, settings

urlpatterns = [
	path('', views.home, name='home'),
	path('signup/', views.signup, name='signup'),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path('logs/<pk>/<container>/', views.logs),
	path('logs/<pk>/', views.logs),
	path('submission/<pk>/', views.submission),
	path('submissions/', views.submissions_list, name='submissions'),
	path('leaderboard/<task>/<phase>/', views.leaderboard, name='leaderboard'),
	path('schedule/<pk>/', views.schedule, name='schedule'),
	path('publications/', include('publications.urls'), name='publications'),
]

if settings.DEBUG:
	urlpatterns += staticfiles_urlpatterns()
