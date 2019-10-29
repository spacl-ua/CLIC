import json

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import StreamingHttpResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from . import models


@csrf_exempt
def status(request, pk, status):
	try:
		submission = models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if request.headers.get('Auth-Token') != submission.auth_token:
		raise PermissionDenied()

	submission.status = status
	submission.save()

	return HttpResponse('', content_type='text/plain')


@csrf_exempt
def results(request, pk):
	try:
		submission = models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if request.headers.get('Auth-Token') != submission.auth_token:
		raise PermissionDenied()

	results = json.loads(request.body)

	return HttpResponse('', content_type='text/plain')
