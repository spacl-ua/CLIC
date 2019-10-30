import json

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db import transaction
from django.http import StreamingHttpResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from . import models


@csrf_exempt
def status(request, pk):
	try:
		submission = models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if request.headers.get('Auth-Token') != submission.auth_token:
		raise PermissionDenied()

	data = json.loads(request.body)

	submission.status = data['status']
	submission.save()

	return HttpResponse(status=200)

@csrf_exempt
def decoding_time(request, pk):
	try:
		submission = models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if request.headers.get('Auth-Token') != submission.auth_token:
		raise PermissionDenied()

	data = json.loads(request.body)

	submission.decoding_time = data['decoding_time']
	submission.save()

	return HttpResponse(status=200)


@csrf_exempt
def metrics(request, pk):
	try:
		submission = models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if request.headers.get('Auth-Token') != submission.auth_token:
		raise PermissionDenied()

	data = json.loads(request.body)

	with transaction.atomic():
		for metric, value in data['metrics'].items():
			measurement = models.Measurement(
				metric=metric,
				value=value,
				submission=submission)
			measurement.save()

	return HttpResponse(status=200)
