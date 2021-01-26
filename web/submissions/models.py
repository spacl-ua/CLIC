import os
import re

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from storages.backends.gcloud import GoogleCloudStorage

from jsonfield import JSONField


class Task(models.Model):
	name = models.CharField(primary_key=True, max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.description


class Phase(models.Model):
	task = models.ForeignKey(Task, on_delete=models.CASCADE)
	name = models.CharField(max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True,
		help_text='Controls whether submissions are currently accepted')
	hidden = models.BooleanField(default=False,
		help_text='Controls whether leaderboard is revealed or not')
	cpu = models.IntegerField(
		help_text='Number of CPUs provided to the decoder', null=False, default=2)
	memory = models.IntegerField(
		help_text='Amount of memory provided to the decoder (MB)', null=False, default=12000)
	timeout = models.IntegerField(
		help_text='Time provided to the decoder (seconds)', null=False, default=36000)
	decoder_fixed = models.BooleanField(default=False,
		help_text='Only allow already submitted decoders to be resubmitted')
	decoder_size_limit = models.BigIntegerField(null=True, blank=True,
		help_text='Optional limit of decoder size (bytes)')
	data_size_limit = models.BigIntegerField(null=True, blank=True,
		help_text='Optional limit of encoded data size (bytes)')
	total_size_limit = models.BigIntegerField(null=True, blank=True,
		help_text='Optional limit of combined file size (bytes)')
	data_fraction = models.FloatField(null=True, blank=True,
		help_text='Fraction of complete dataset (used to estimate total dataset size)')
	settings = JSONField(blank=True, default='')

	def __str__(self):
		return '{0} ({1})'.format(self.task, self.description.lower())


class DockerImage(models.Model):
	name = models.CharField(max_length=256)
	gpu = models.BooleanField(default=False)
	active = models.BooleanField(default=True,
		help_text='Controls whether docker image can be selected by non-staff users')

	def __str__(self):
		return '{0} ({1})'.format(self.name, 'GPU' if self.gpu else 'CPU')


class Submission(models.Model):
	STATUS_ERROR = 0
	STATUS_WAITING = 10
	STATUS_DECODING = 20
	STATUS_DECODING_FAILED = 30
	STATUS_DECODED = 40
	STATUS_EVALUATING = 50
	STATUS_EVALUATION_FAILED = 60
	STATUS_SUCCESS = 70
	STATUS_CANCELED = 80
	STATUS_CHOICES = [
			(STATUS_ERROR, 'Error'),
			(STATUS_WAITING, 'Waiting'),
			(STATUS_DECODING, 'Decoding'),
			(STATUS_DECODING_FAILED, 'Decoding failed'),
			(STATUS_DECODED, 'Decoded'),
			(STATUS_EVALUATING, 'Evaluating'),
			(STATUS_EVALUATION_FAILED, 'Evaluation failed'),
			(STATUS_SUCCESS, 'Success'),
			(STATUS_CANCELED, 'Canceled'),
		]
	STATUS_ICONS = [
			(STATUS_ERROR, 'fas fa-bug text-danger'),
			(STATUS_WAITING, 'fas fa-clock'),
			(STATUS_DECODING, 'fas fa-circle-notch fa-spin text-primary'),
			(STATUS_DECODING_FAILED, 'fas fa-exclamation-circle text-danger'),
			(STATUS_DECODED, 'fas fa-circle-notch fa-spin text-primary'),
			(STATUS_EVALUATING, 'fas fa-circle-notch fa-spin text-primary'),
			(STATUS_EVALUATION_FAILED, 'fas fa-exclamation-circle text-danger'),
			(STATUS_SUCCESS, 'fas fa-check-circle text-success'),
			(STATUS_CANCELED, 'fas fa-times text-warning'),
		]
	STATUS_IN_PROGRESS = [STATUS_WAITING, STATUS_DECODING, STATUS_DECODED, STATUS_EVALUATING]

	timestamp = models.DateTimeField(auto_now_add=True)
	team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
	docker_image = models.ForeignKey(DockerImage, on_delete=models.PROTECT)
	task = models.ForeignKey(Task, on_delete=models.PROTECT)
	phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
	decoder_hash = models.CharField(max_length=128)
	decoder_size = models.IntegerField()
	decoding_time = models.IntegerField(null=True, blank=True)
	data_size = models.IntegerField()
	hidden = models.BooleanField(default=False)
	status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_WAITING)
	link = models.CharField(max_length=512, blank=True)

	def job_name(self):
		"""
		Name used for Kubernetes jobs
		"""
		name = 'run-{task}-{phase}-{team}'.format(
			task=self.task.name.lower(),
			phase=self.phase.name.lower(),
			team=self.team.username.lower())

		# apply restrictions of Kubernetes
		return re.sub('[^a-zA-Z0-9.-]', '', name)[:253]

	def fs_path(self):
		"""
		Path to where submission is stored
		"""
		return os.path.join(self.task.name, self.phase.name, self.team.username, str(self.id))

	def status_icon(self):
		"""
		https://fontawesome.com/icons
		"""
		return dict(self.STATUS_ICONS).get(self.status, 'question')

	def measurements(self):
		"""
		Returns evaluation results as a dictionary
		"""
		m_all = {}
		for m in self.measurement_set.all():
			m_all[m.metric] = m.value
		return m_all

	def in_progress(self):
		return self.status in self.STATUS_IN_PROGRESS


@receiver(post_delete, sender=Submission, dispatch_uid='delete_submission')
def delete_submission(sender, instance, **kwargs):
	# delete files corresponding to submission
	fs = GoogleCloudStorage(bucket_name=settings.GS_BUCKET_SUBMISSIONS)
	blobs = fs.bucket.list_blobs(prefix=instance.fs_path())
	for blob in blobs:
		blob.delete()


class Measurement(models.Model):
	timestamp = models.DateField(auto_now_add=True)
	metric = models.CharField(max_length=128)
	value = models.FloatField()
	submission = models.ForeignKey(Submission, on_delete=models.CASCADE)

	def better_than(self, measurement):
		if measurement is None:
			return True
		if self.metric in ['FID', 'KID']:
			return self.value < measurement.value
		return self.value > measurement.value
