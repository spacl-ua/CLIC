import os
import yaml

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.template.loader import get_template
from django.http import StreamingHttpResponse, Http404
from storages.backends.gcloud import GoogleCloudStorage
from kubernetes.client.rest import ApiException

import teams
import submissions
import submissions.forms
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
	if request.user.is_authenticated:
		if request.method == 'POST':
			form = submissions.forms.SubmitForm(request.POST, request.FILES)

			if form.is_valid():
				# upload files to storage bucket
				fs = GoogleCloudStorage()
				for file in request.FILES.getlist('files'):
					fs.save(
						name=os.path.join(
							form.cleaned_data.get('task'),
							form.cleaned_data.get('phase'),
							request.user.username,
							file.name),
						content=file)

					# create job
					job_template = get_template('job.yaml')
					job = yaml.load(job_template.render())

					# submit job
					client = KubernetesClient()
					try:
						client.delete_job(job)
					except ApiException:
						pass

					client.create_job(job)

				return redirect('home')
		else:
			form = submissions.forms.SubmitForm()
	else:
		form = teams.forms.AuthenticationForm()

	return render(request, 'home.html', {'form': form})


def logs(request, team, task, phase, container):
	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user.username != 'team' and not request.user.is_staff:
		raise PermissionDenied()

	client = KubernetesClient()

	# find corresponding pods
	job_name = f'run-{task}-{phase}-{team}'
	pods = client.list_pods(label_selector=f'job-name={job_name}')

	if len(pods) == 0:
		raise Http404('Could not find logs.')

	# stream logs
	logs = client.read_log(pods[0], container=container, follow=True)
	return StreamingHttpResponse(logs, content_type='text/plain')
