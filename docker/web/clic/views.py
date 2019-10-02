from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate

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
		form = submissions.forms.SubmitForm()
	else:
		form = teams.forms.AuthenticationForm()
	return render(request, 'home.html', {'form': form})
