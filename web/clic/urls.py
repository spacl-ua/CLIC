from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic.base import RedirectView

from . import views, settings

urlpatterns = [
	path('submit/', views.submit, name='submit'),
	path('signup/', views.signup, name='signup'),
	path('admin/', admin.site.urls),
	path('accounts/', include('django.contrib.auth.urls')),
	path('logs/<pk>/<container>/', views.logs),
	path('logs/<pk>/', views.logs),
	path('reevaluate/<pk>/', views.reevaluate),
	path('submission/<pk>/', views.submission),
	path('submissions/', views.submissions_list, name='submissions'),
	path('leaderboard/<task>/<phase>/', views.leaderboard, name='leaderboard'),
	path('leaderboard/', RedirectView.as_view(url='/leaderboard/lowrate/test/', permanent=False)),
	path('schedule/<pk>/', views.schedule, name='schedule'),
	path('publications/', include('publications.urls'), name='publications'),
]

if settings.DEBUG:
	import debug_toolbar
	urlpatterns += staticfiles_urlpatterns()
	urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
