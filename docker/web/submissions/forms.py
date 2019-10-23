from django import forms
from django.core.exceptions import ValidationError

import teams
from . import models


class SubmitForm(forms.Form):
	team = forms.ModelChoiceField(
		teams.models.Team.objects.all(), empty_label=None)
	phase = forms.ModelChoiceField(
		models.Phase.objects.filter(active=True), empty_label=None,
		label="Task and phase")
	decoder = forms.FileField(
		help_text='An executable or a zip file containing an executable named \'decode\'')
	data = forms.FileField(
		widget=forms.ClearableFileInput(attrs={'multiple': True}),
		help_text='Files representing the encoded images')
	docker_image = forms.ModelChoiceField(models.DockerImage.objects.all(), empty_label=None,
		help_text='The environment in which your decoder will be run')
	hidden = forms.BooleanField(help_text='Hide submission from leaderboard', required=False)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)

		super(SubmitForm, self).__init__(*args, **kwargs)

		if getattr(self.user, 'is_staff', False):
			self.fields['phase'].queryset = models.Phase.objects.order_by('task').all()
		else:
			# remove fields only staff should be able to see
			del self.fields['team']
			del self.fields['hidden']


	def clean_data(self):
		if self.files is None:
			raise ValidationError('Please select at least 1 file.')
		for file in self.files.getlist('data'):
			if file.name == 'decode' or file.name == 'decoder.zip':
				raise ValidationError('Data files cannot be named \'decode\' or \'decoder.zip\'')
		return self.files


	def clean_phase(self):
		self.cleaned_data['task'] = self.cleaned_data['phase'].task
		return self.cleaned_data['phase']


	def clean(self):
		super().clean()
		if not getattr(self.user, 'is_staff', False):
			self.cleaned_data['team'] = self.user
			self.cleaned_data['hidden'] = False
		return self.cleaned_data
