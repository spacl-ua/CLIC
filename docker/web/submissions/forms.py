from django import forms
from django.core.exceptions import ValidationError

import teams


class SubmitForm(forms.Form):
	team = forms.ModelChoiceField(teams.models.Team.objects.all(), empty_label=None)
	task = forms.ChoiceField(choices=[('lowrate', 'lowrate'), ('pframe', 'pframe')])
	phase = forms.ChoiceField(choices=[('valid', 'validation'), ('test', 'test')])
	decoder = forms.FileField(
		help_text='An executable or a zip file containing an executable named \'decode\'')
	data = forms.FileField(
		widget=forms.ClearableFileInput(attrs={'multiple': True}),
		help_text='Files representing the encoded images')
	gpu = forms.BooleanField(
		label='GPU', required=False, help_text='Tick this if your decoder requires a GPU')
	hidden = forms.BooleanField(help_text='Hide submission from leaderboard', required=False)

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)

		super(SubmitForm, self).__init__(*args, **kwargs)

		# remove fields only staff should be able to see
		if user is None or not user.is_staff:
			del self.fields['team']
			del self.fields['hidden']

	def clean_data(self):
		if self.files is None:
			raise ValidationError('Please select at least 1 file.')
		for file in self.files.getlist('data'):
			if file.name == 'decode' or file.name == 'decoder.zip':
				raise ValidationError('Data files cannot be named \'decode\' or \'decoder.zip\'')
