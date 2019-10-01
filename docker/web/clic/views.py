from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate

from teams import forms


def signup(request):
	if request.method == 'POST':
		form = forms.TeamCreationForm(request.POST)

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
		form = forms.TeamCreationForm()

	return render(request, 'registration/signup.html', {'form': form})


def home(request):
	form = forms.AuthenticationForm()
	return render(request, 'home.html', {'form': form})
