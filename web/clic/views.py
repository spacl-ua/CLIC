import os
import yaml

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.template.loader import get_template
from django.http import StreamingHttpResponse, HttpResponse, Http404
from storages.backends.gcloud import GoogleCloudStorage
from kubernetes.client.rest import ApiException

import teams
import submissions
import submissions.forms
import submissions.models
from .kubernetes_client import KubernetesClient


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

			return redirect('home')
	else:
		form = teams.forms.TeamCreationForm()

	return render(request, 'registration/signup.html', {'form': form})


def home(request):
	status = 200

	if request.user.is_authenticated:
		if request.method == 'POST':
			form = submissions.forms.SubmitForm(
				request.POST,
				request.FILES,
				user=request.user)

			if form.is_valid():
				return submit(request, form)
			else:
				status = 422
		else:
			form = submissions.forms.SubmitForm(
				user=request.user,
				initial={'team': request.user.id})
	else:
		form = teams.forms.AuthenticationForm()

	return render(request, 'home.html', {'form': form}, status=status)


def submit(request, form):
	"""
	Creates a kubernetes job running the decoder
	"""

	if not request.user.is_authenticated:
		raise PermissionDenied()

	if not request.user.is_staff:
		# only staff is allowed to choose these
		if form.cleaned_data['team'] != request.user:
			raise PermissionDenied()
		if not form.cleaned_data['phase'].active:
			raise PermissionDenied()
		if not form.cleaned_data['task'].active:
			raise PermissionDenied()

	# create entry in database
	submission = submissions.models.Submission(
		team=form.cleaned_data['team'],
		task=form.cleaned_data['task'],
		phase=form.cleaned_data['phase'],
		docker_image=form.cleaned_data['docker_image'],
		hidden=form.cleaned_data['hidden'],
		decoder_size=form.cleaned_data['decoder_size'],
		decoder_hash=form.cleaned_data['decoder_hash'],
		data_size=form.cleaned_data['data_size'])
	submission.save()

	# submission will be stored here
	fs = GoogleCloudStorage()
	fs_path = submission.fs_path()

	# upload encoded image files to storage bucket
	for file in request.FILES.getlist('data'):
		print('Saving {0}'.format(os.path.join(fs_path, file.name)))
		fs.save(name=os.path.join(fs_path, file.name), content=file)

	# upload decoder to storage bucket
	if request.FILES['decoder'].name.lower().endswith('.zip'):
		fs.save(name=os.path.join(fs_path, 'decoder.zip'), content=request.FILES['decoder'])
	else:
		print('Saving {0}'.format(os.path.join(fs_path, 'decode')))
		fs.save(name=os.path.join(fs_path, 'decode'), content=request.FILES['decoder'])

	# create job
	job_template = get_template('job.yaml')
	job = yaml.load(job_template.render({'submission': submission}))

	# submit job
	client = KubernetesClient()
	try:
		client.delete_job(job)
	except ApiException:
		pass
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
		return HttpResponse('Logs are no longer available.', content_type='text/event-stream')

	# stream logs
	try:
		logs = client.stream_log(pods[0], container=container)
	except ApiException:
		# container may yet have to start
		raise Http404('Could not find logs.')

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
	if request.user.username != submission.team and not request.user.is_staff:
		raise PermissionDenied()

	return render(request, 'submission.html', {'submission': submission})
