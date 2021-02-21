import os
import yaml
from collections import defaultdict

from django.contrib.auth import login, authenticate
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db import transaction
from django.http import StreamingHttpResponse, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.utils.crypto import get_random_string
from storages.backends.gcloud import GoogleCloudStorage

import teams
import submissions.forms
import submissions.models
from .kubernetes_client import KubernetesClient
from . import models


def signup(request):
	if request.method == 'POST':
		form = teams.forms.TeamCreationForm(request.POST)

		if form.is_valid():
			# create team
			form.save()

			# login team
			user = authenticate(
				username=form.cleaned_data.get('username'),
				password=form.cleaned_data.get('password1'))
			login(request, user)

			return redirect('submit')
	else:
		form = teams.forms.TeamCreationForm()

	return render(request, 'registration/signup.html', {'form': form})


def submit(request):
	status = 200

	if request.user.is_authenticated:
		if request.method == 'POST':
			form = submissions.forms.SubmitForm(
				request.POST,
				request.FILES,
				user=request.user)

			if form.is_valid():
				return _decode(request, **form.cleaned_data)
			else:
				status = 422
		else:
			form = submissions.forms.SubmitForm(
				user=request.user,
				initial={'team': request.user.id})
	else:
		form = teams.forms.AuthenticationForm()

	return render(request, 'submit.html', {'form': form}, status=status)


def _decode(request, **kwargs):
	"""
	Creates a kubernetes job running the decoder and the evaluation
	"""

	if not request.user.is_authenticated:
		raise PermissionDenied()

	if not request.user.is_staff:
		# only staff is allowed to choose these
		if kwargs['team'] != request.user:
			raise PermissionDenied()
		if not kwargs['phase'].active:
			raise PermissionDenied()
		if not kwargs['task'].active:
			raise PermissionDenied()

	# create entry in database
	submission = submissions.models.Submission(
		team=kwargs['team'],
		task=kwargs['task'],
		phase=kwargs['phase'],
		docker_image=kwargs['docker_image'],
		hidden=kwargs['hidden'],
		decoder_size=kwargs['decoder_size'],
		decoder_hash=kwargs['decoder_hash'],
		data_size=kwargs['data_size'])
	submission.save()

	# submission will be stored here
	fs = GoogleCloudStorage(bucket_name=settings.GS_BUCKET_SUBMISSIONS)
	fs_path = submission.fs_path()

	# upload encoded image files to storage bucket
	for file in request.FILES.getlist('data'):
		fs.save(name=os.path.join(fs_path, file.name), content=file)

	if 'decoder' in request.FILES:
		# upload decoder to storage bucket
		if request.FILES['decoder'].name.lower().endswith('.zip'):
			fs.save(
				name=os.path.join(fs_path, 'decoder.zip'),
				content=request.FILES['decoder'])
		else:
			fs.save(
				name=os.path.join(fs_path, 'decode'),
				content=request.FILES['decoder'])
	else:
		# no decoder provided, use dummy
		fs.save(
			name=os.path.join(fs_path, 'decode'),
			content=ContentFile(b'#!/bin/bash'))

	# create job
	job_template = get_template('job.yaml')
	job = yaml.load(job_template.render({
		'submission': submission,
		'debug': request.user.is_staff}))

	# submit job
	client = KubernetesClient()
	client.delete_job(job)
	client.create_job(job)

	# mark running submission(s) as canceled
	subs = submissions.models.Submission.objects.filter(
		team=kwargs['team'],
		task=kwargs['task'],
		phase=kwargs['phase'],
		status__in=submissions.models.Submission.STATUS_IN_PROGRESS)
	subs = subs.exclude(id=submission.id)
	with transaction.atomic():
		for sub in subs:
			sub.status = submissions.models.Submission.STATUS_CANCELED
			sub.save()

	return HttpResponse(
		'{{"location": "/submission/{pk}/"}}'.format(pk=submission.pk),
		content_type='application/json')


def reevaluate(request, pk):
	"""
	Creates a kubernetes job running only the evaluation
	"""

	if not request.user.is_staff:
		# only staff is allowed to restart an evaluation
		raise PermissionDenied()

	try:
		submission = submissions.models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	# submission is stored here
	fs = GoogleCloudStorage(bucket_name=settings.GS_BUCKET_SUBMISSIONS)
	fs_path = submission.fs_path()

	# create job
	job_template = get_template('job.yaml')
	job = yaml.load(job_template.render({
    'eval_only': True,
		'submission': submission,
		'debug': request.user.is_staff}))

	# submit job
	client = KubernetesClient()
	client.delete_job(job)
	client.create_job(job)

	return HttpResponse(
		'{{"location": "/submission/{pk}/"}}'.format(pk=submission.pk),
		content_type='application/json')


def logs(request, pk, container=['decode', 'evaluate']):
	"""
	Streams logs of running submissions
	"""

	try:
		submission = submissions.models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user != submission.team and not request.user.is_staff:
		raise PermissionDenied()

	client = KubernetesClient()

	# find corresponding pods
	pods = client.list_pods(label_selector=f'id={submission.id}')

	if len(pods) == 0:
		# pods are gone, try to load logs stored with the submission
		fs = GoogleCloudStorage(bucket_name=settings.GS_BUCKET_SUBMISSIONS)
		fs_path = submission.fs_path()

		log_path_decode = os.path.join(fs_path, '.log_decode')
		log_path_eval = os.path.join(fs_path, '.log_evaluate')

		logs = b''
		if fs.exists(log_path_decode):
			with fs.open(log_path_decode) as handle:
				logs += handle.read()
				logs += b'\n'
		if fs.exists(log_path_eval):
			with fs.open(log_path_eval) as handle:
				logs += handle.read()

		if logs:
			return HttpResponse(logs, content_type='text/plain')

		return HttpResponse('Logs are no longer available.', content_type='text/plain')

	# stream logs
	logs = client.stream_log(pods[0], container=container)

	if 'Gecko' in request.META['HTTP_USER_AGENT']:
		# Firefox will try to download a text/event-stream
		response = StreamingHttpResponse(logs, content_type='text/plain')
		response['X-Content-Type-Options'] = 'nosniff'
		return response
	return StreamingHttpResponse(logs, content_type='text/event-stream')


def submission(request, pk):
	"""
	Allows a team to view its latest submission
	"""

	try:
		submission = submissions.models.Submission.objects.get(pk=pk)
	except ObjectDoesNotExist:
		raise Http404('Could not find submission.')

	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user != submission.team and not request.user.is_staff:
		raise PermissionDenied()

	measurements = submissions.models.Measurement.objects.filter(submission=submission)

	return render(request, 'submission.html', {
		'submission': submission,
		'measurements': measurements})


def submissions_list(request):
	"""
	List all submissions of a user.
	"""

	if not request.user.is_authenticated:
		raise PermissionDenied()

	subs = submissions.models.Submission.objects.filter(team=request.user).order_by('-timestamp')
	subs = subs.prefetch_related('task', 'phase', 'measurement_set')

	metrics = set()
	for sub in subs:
		for measurement in sub.measurement_set.all():
			metrics.add(measurement.metric)

	return render(request, 'submissions.html', {'metrics': metrics, 'submissions': subs})


def leaderboard(request, task, phase):
	try:
		task = submissions.models.Task.objects.filter(name=task)[0]
		phase = submissions.models.Phase.objects.filter(name=phase, task=task)[0]
		phase.task = task
	except IndexError:
		raise Http404('Could not find task.')

	if phase.hidden and not request.user.is_staff:
		raise PermissionDenied()

	subs = submissions.models.Submission.objects.filter(
		phase=phase,
		hidden=False,
		status=submissions.models.Submission.STATUS_SUCCESS)
	subs = subs.prefetch_related('measurement_set').select_related('team')
	subs_best = defaultdict(lambda: None)

	metrics = set()
	for sub in subs:
		for measurement in sub.measurement_set.all():
			# keep submission if it dominates others in at least one metric
			if measurement.better_than(subs_best[sub.team, measurement.metric]):
				subs_best[sub.team, measurement.metric] = measurement
			# collect metrics
			metrics.add(measurement.metric)
	subs_best = {measurement.submission for measurement in subs_best.values()}


	phases = submissions.models.Phase.objects.filter(hidden=False).order_by('task')
	phases = phases.prefetch_related('task')

	for p in phases:
		p.current = (p.id == phase.id)

	return render(request, 'leaderboard.html', {
			'phases': phases,
			'phase': phase,
			'metrics': metrics,
			'submissions': subs_best,
		})


def schedule(request, pk):
	schedule = models.Schedule.objects.get(pk=pk)
	if request.GET.get('format', '').lower() == 'json':
		return render(request, 'schedule.json', {'schedule': schedule}, content_type='application/json')
	return render(request, 'schedule.html', {'schedule': schedule})
