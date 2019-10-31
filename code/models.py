"""
Copy of models used by Django webserver.
"""

import os

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser, UserManager


class TeamManager(UserManager):
	def get_by_natural_key(self, username):
		case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
		return self.get(**{case_insensitive_username_field: username})


class Team(AbstractUser):
	class Meta:
		app_label = 'teams'

	def __str__(self):
		return self.username


class Task(models.Model):
	class Meta:
		app_label = 'submissions'

	name = models.CharField(primary_key=True, max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.description


class Phase(models.Model):
	class Meta:
		app_label = 'submissions'

	task = models.ForeignKey(Task, on_delete=models.CASCADE)
	name = models.CharField(max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True,
		help_text='Controls whether submissions are currently accepted')
	decoder_fixed = models.BooleanField(default=False,
		help_text='Only allow already submitted decoders to be resubmitted')
	decoder_size_limit = models.IntegerField(null=True, blank=True)
	data_size_limit = models.IntegerField(null=True, blank=True)

	def __str__(self):
		return '{0} ({1})'.format(self.task, self.description)


class DockerImage(models.Model):
	class Meta:
		app_label = 'submissions'

	name = models.CharField(max_length=256)
	gpu = models.BooleanField(default=False)
	active = models.BooleanField(default=True,
		help_text='Controls whether docker image can be selected by non-staff users')

	def __str__(self):
		return '{0} ({1})'.format(self.name, 'GPU' if self.gpu else 'CPU')


class Submission(models.Model):
	class Meta:
		app_label = 'submissions'

	STATUS_ERROR = 0
	STATUS_CREATED = 10
	STATUS_DECODING = 20
	STATUS_DECODING_FAILED = 30
	STATUS_DECODED = 40
	STATUS_EVALUATING = 50
	STATUS_EVALUATION_FAILED = 60
	STATUS_SUCCESS = 70
	STATUS_CHOICES = [
			(STATUS_ERROR, 'Error'),
			(STATUS_CREATED, 'Created'),
			(STATUS_DECODING, 'Decoding'),
			(STATUS_DECODING_FAILED, 'Decoding failed'),
			(STATUS_DECODED, 'Decoded'),
			(STATUS_EVALUATING, 'Evaluating'),
			(STATUS_EVALUATION_FAILED, 'Evaluation failed'),
			(STATUS_SUCCESS, 'Success'),
		]

	timestamp = models.DateTimeField(auto_now_add=True)
	team = models.ForeignKey(Team, on_delete=models.CASCADE)
	docker_image = models.ForeignKey(DockerImage, on_delete=models.PROTECT)
	task = models.ForeignKey(Task, on_delete=models.PROTECT)
	phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
	decoder_hash = models.CharField(max_length=128)
	decoder_size = models.IntegerField()
	decoding_time = models.IntegerField(null=True)
	data_size = models.IntegerField()
	hidden = models.BooleanField(default=False)
	status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_CREATED)

	def fs_path(self):
		"""
		Path to where submission is stored
		"""
		return os.path.join(self.task.name, self.phase.name, self.team.username, str(self.id))


class Measurement(models.Model):
	class Meta:
		app_label = 'submissions'

	timestamp = models.DateField(auto_now_add=True)
	metric = models.CharField(max_length=128)
	value = models.FloatField()
	submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
