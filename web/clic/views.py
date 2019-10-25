import os
import yaml

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
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
	Creates a kubernetes job running the decoder.
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

	job_description = {
		'team': form.cleaned_data['team'].username.lower(),
		'task': form.cleaned_data['task'].name.lower(),
		'phase': form.cleaned_data['phase'].name.lower(),
		'image': form.cleaned_data['docker_image'].name,
		'gpu': form.cleaned_data['docker_image'].gpu}

	# submission will be stored here
	fs = GoogleCloudStorage()
	fs_path = os.path.join(
		job_description['task'],
		job_description['phase'],
		job_description['team'])

	# delete previous submission, if it exists
	blobs = fs.bucket.list_blobs(prefix=fs_path)
	for blob in blobs:
		blob.delete()

	# upload encoded image files to storage bucket
	for file in request.FILES.getlist('data'):
		fs.save(name=os.path.join(fs_path, file.name), content=file)

	# upload decoder to storage bucket
	if request.FILES['decoder'].name.lower().endswith('.zip'):
		fs.save(name=os.path.join(fs_path, 'decoder.zip'), content=request.FILES['decoder'])
	else:
		fs.save(name=os.path.join(fs_path, 'decode'), content=request.FILES['decoder'])

	# create job
	job_template = get_template('job.yaml')
	job = yaml.load(job_template.render(job_description))

	# submit job
	client = KubernetesClient()
	try:
		client.delete_job(job)
	except ApiException:
		pass
	client.create_job(job)

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

	return HttpResponse(
		'{{"location": "/submission/{task}/{phase}/{team}/"}}'.format(**job_description),
		content_type='application/json')


def logs(request, task, phase, team, container=None):
	"""
	Streams logs of running submissions.
	"""

	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user.username.lower() != team.lower() and not request.user.is_staff:
		raise PermissionDenied()
	if container not in ['decode', 'evaluate', None]:
		raise Http404('Could not find logs.')

	if container is None:
		# return both logs concatenated
		container = ['decode', 'evaluate']

	client = KubernetesClient()

	# find corresponding pods
	job_name = f'run-{task}-{phase}-{team}'.lower()
	pods = client.list_pods(label_selector=f'job-name={job_name}')

	if len(pods) == 0:
		raise Http404('Could not find logs.')

	# stream logs
	try:
		logs = client.stream_log(pods[0], container=container)
	except ApiException:
		# container may yet have to start
		raise Http404('Could not find logs.')

	return StreamingHttpResponse(logs, content_type='text/event-stream')


def submission(request, task, phase, team):
	"""
	Allows a team to view its latest submission.
	"""

	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user.username.lower() != team.lower() and not request.user.is_staff:
		raise PermissionDenied()

	return render(request, 'submission.html', {'team': team, 'task': task, 'phase': phase})
