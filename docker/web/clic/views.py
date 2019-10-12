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
			form = submissions.forms.SubmitForm(
				request.POST,
				request.FILES,
				user=request.user)

			if form.is_valid():
				if request.user.is_staff:
					# staff can choose team freely
					team_name = teams.models.Team.objects.get(id=form.cleaned_data['team']).username
				else:
					team_name = request.user.username

				fs = GoogleCloudStorage()
				fs_path = os.path.join(
					form.cleaned_data['task'].lower(),
					form.cleaned_data['phase'].lower(),
					team_name.lower())

				# delete previous submission
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
				job_identifier = {
						'task': form.cleaned_data['task'].lower(),
						'phase': form.cleaned_data['phase'].lower(),
						'team': team_name.lower()}
				job = yaml.load(job_template.render(job_identifier))

				# submit job
				client = KubernetesClient()
				try:
					client.delete_job(job)
				except ApiException:
					pass
				client.create_job(job)

				return redirect('/submission/{task}/{phase}/{team}/'.format(**job_identifier))
		else:
			form = submissions.forms.SubmitForm(
				user=request.user,
				initial={'team': request.user.id})
	else:
		form = teams.forms.AuthenticationForm()

	return render(request, 'home.html', {'form': form})


def logs(request, team, task, phase, container):
	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user.username.lower() != team.lower() and not request.user.is_staff:
		raise PermissionDenied()

	client = KubernetesClient()

	# find corresponding pods
	job_name = f'run-{task}-{phase}-{team}'.lower()
	pods = client.list_pods(label_selector=f'job-name={job_name}')

	if len(pods) == 0:
		raise Http404('Could not find logs.')

	# stream logs
	logs = client.read_log(pods[0], container=container, follow=True)
	return StreamingHttpResponse(logs, content_type='text/plain')


def submission(request, team, task, phase):
	if not request.user.is_authenticated:
		raise PermissionDenied()
	if request.user.username.lower() != team.lower() and not request.user.is_staff:
		raise PermissionDenied()

	return render(request, 'submission.html', {'team': team, 'task': task, 'phase': phase})
