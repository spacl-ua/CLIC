from django import forms
from django.contrib import auth

from . import models


class TeamCreationForm(auth.forms.UserCreationForm):
	class Meta:
		model = models.Team
		fields = ('username', 'email', 'affiliation', 'members')

	username = forms.CharField(label='Team name', max_length=32)


class TeamChangeForm(auth.forms.UserChangeForm):
	class Meta:
		model = models.Team
		fields = ('username', 'email', 'affiliation', 'members')


class AuthenticationForm(auth.forms.AuthenticationForm):
	class Meta:
		model = models.Team
		fields = ('username', 'email')
