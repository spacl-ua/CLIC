from django import forms
from django.core.exceptions import ValidationError

import teams
from . import models, utils


class MultipleFileInput(forms.ClearableFileInput):
	allow_multiple_selected = True


class MultipleFileField(forms.FileField):
	def __init__(self, *args, **kwargs):
		kwargs.setdefault("widget", MultipleFileInput())
		super().__init__(*args, **kwargs)

	def clean(self, data, initial=None):
		single_file_clean = super().clean
		if isinstance(data, (list, tuple)):
			result = [single_file_clean(d, initial) for d in data]
		else:
			result = single_file_clean(data, initial)
		return result


class SubmitForm(forms.Form):
	team = forms.ModelChoiceField(
		teams.models.Team.objects.all(),
		empty_label=None)
	phase = forms.ModelChoiceField(
		models.Phase.objects.filter(active=True),
		empty_label=None,
		label="Task and phase")
	decoder = forms.FileField(
		required=False,
		help_text='An executable or a zip file containing an executable named \'decode\'')
	data = MultipleFileField(
		help_text='Files representing the encoded images')
	docker_image = forms.ModelChoiceField(
		models.DockerImage.objects.filter(active=True),
		empty_label=None,
		help_text='The environment in which your decoder will be run')
	hidden = forms.BooleanField(
		help_text='Hide submission from leaderboard',
		required=False)
	permission = forms.BooleanField(
		label='We grant permission to publish reconstructions ',
		help_text= \
			'We will only publish reconstructed PNGs, <u>not</u> your decoder. ' \
			'Images will be released under the '
			'<a href="https://data.vision.ee.ethz.ch/cvl/clic/LICENSE_professional_2020.txt">Unsplash license</a>. ' \
			'Videos will be released under a ' \
			'<a href="https://creativecommons.org/share-your-work/public-domain/cc0/">CC0 license</a>.',
		required=False)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)

		super(SubmitForm, self).__init__(*args, **kwargs)

		if getattr(self.user, 'is_staff', False):
			# make all tasks and phases available to staff
			self.fields['phase'].queryset = \
				models.Phase.objects.order_by('task').all().select_related('task')
			self.fields['docker_image'].queryset = models.DockerImage.objects.all()
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

		self.cleaned_data['data_size'] = 0
		for file in self.files.getlist('data'):
			self.cleaned_data['data_size'] += file.size

		if 'decoder' in self.files:
			self.cleaned_data['decoder_size'] = self.files['decoder'].size
			self.cleaned_data['decoder_hash'] = utils.hash_uploaded_file(self.files['decoder'])
		else:
			self.cleaned_data['decoder_size'] = 0
			self.cleaned_data['decoder_hash'] = ''

		if self.cleaned_data['phase'].decoder_fixed:
			submissions = models.Submission.objects.filter(
				decoder_hash=self.cleaned_data['decoder_hash'])
			if submissions.count() < 1:
				error = ValidationError(
					'The decoder has to correspond to a previously submitted decoder')
				self.add_error('decoder', error)

		if self.cleaned_data['phase'].decoder_size_limit:
			if self.cleaned_data['decoder_size'] > self.cleaned_data['phase'].decoder_size_limit:
				error = ValidationError(
					'Decoder should contain at most {1} bytes but contains {0} bytes'.format(
						self.cleaned_data['decoder_size'],
						self.cleaned_data['phase'].decoder_size_limit))
				self.add_error('decoder', error)

		if self.cleaned_data['phase'].data_size_limit:
			if self.cleaned_data['data_size'] > self.cleaned_data['phase'].data_size_limit:
				error = ValidationError(
					'Data should contain less than {1} bytes but contains {0} bytes'.format(
						self.cleaned_data['data_size'],
						self.cleaned_data['phase'].data_size_limit))
				self.add_error('data', error)

		if self.cleaned_data['phase'].total_size_limit:
			if self.cleaned_data['phase'].data_fraction:
				total_size = self.cleaned_data['data_size'] / self.cleaned_data['phase'].data_fraction \
					+ self.cleaned_data['decoder_size']
				total_size = int(total_size)
				if total_size > self.cleaned_data['phase'].total_size_limit:
					error = ValidationError(
						'Total file size should be less than {1} bytes but is estimated to be {0} bytes'.format(
							total_size,
							self.cleaned_data['phase'].total_size_limit))
					self.add_error('data', error)
			else:
				total_size = self.cleaned_data['data_size'] + self.cleaned_data['decoder_size']
				if total_size > self.cleaned_data['phase'].total_size_limit:
					error = ValidationError(
						'Combined file size should be less than {1} bytes but is {0} bytes'.format(
							total_size,
							self.cleaned_data['phase'].total_size_limit))
					self.add_error('data', error)

		if self.cleaned_data['phase'].ask_permission == 'required':
			if not self.cleaned_data.get('permission', False):
				error = ValidationError('Permission to publish is required for this track')
				self.add_error('permission', error)

		if 'permission' not in self.cleaned_data:
			self.cleaned_data['permission'] = False

		return self.cleaned_data
