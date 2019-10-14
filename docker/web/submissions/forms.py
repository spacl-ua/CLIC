from django import forms
from django.core.exceptions import ValidationError

import teams


def validate_submission_data_field(values):
	for value in values:
		if value == 'decode' or value == 'decoder.zip':
			raise ValidationError('Data files cannot be named \'decode\' or \'decoder.zip\'.')


class SubmitForm(forms.Form):
	team = forms.ModelChoiceField(teams.models.Team.objects.all(), empty_label=None)
	task = forms.ChoiceField(choices=[('lowrate', 'lowrate'), ('pframe', 'pframe')])
	phase = forms.ChoiceField(choices=[('valid', 'validation'), ('test', 'test')])
	decoder = forms.FileField(
		help_text='An executable or a zip file containing an executable named \'decode\'.')
	gpu = forms.BooleanField(label='Requires GPU', required=False)
	data = forms.FileField(
		validators=[validate_submission_data_field],
		widget=forms.ClearableFileInput(attrs={'multiple': True}),
		help_text='The encoded image files.')
	hidden = forms.BooleanField(help_text='Hide submission from leaderboard.', required=False)

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)

		super(SubmitForm, self).__init__(*args, **kwargs)

		# remove fields only staff should be able to see
		if user is None or not user.is_staff:
			del self.fields['team']
			del self.fields['hidden']
