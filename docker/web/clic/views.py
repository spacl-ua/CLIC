import os

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.files.storage import default_storage

from storages.backends.gcloud import GoogleCloudStorage

import teams
import submissions
import submissions.forms


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
				fs = GoogleCloudStorage()
				# upload files
				for file in request.FILES.getlist('files'):
					fs.save(
						name=os.path.join(
							form.cleaned_data.get('task'),
							form.cleaned_data.get('phase'),
							request.user.username,
							file.name),
						content=file)

				return redirect('home')
		else:
			form = submissions.forms.SubmitForm()
	else:
		form = teams.forms.AuthenticationForm()

	return render(request, 'home.html', {'form': form})
