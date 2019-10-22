from django.db import models


class Task(models.Model):
	name = models.CharField(primary_key=True, max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.description


class Phase(models.Model):
	name = models.CharField(primary_key=True, max_length=32)
	description = models.CharField(max_length=32)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.description


class DockerImage(models.Model):
	name = models.CharField(max_length=256)
	gpu = models.BooleanField(default=False)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.name


class Submission(models.Model):
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

	timestamp = models.DateField(auto_now_add=True)
	team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
	docker_image = models.ForeignKey(DockerImage, on_delete=models.PROTECT)
	task = models.ForeignKey(Task, on_delete=models.PROTECT)
	phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
	gpu = models.BooleanField(default=False)
	decoder_hash = models.CharField(max_length=128)
	decoder_size = models.IntegerField()
	decoding_time = models.IntegerField()
	data_size = models.IntegerField()
	hidden = models.BooleanField(default=False)
	status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CREATED)


class Measurement(models.Model):
	timestamp = models.DateField(auto_now_add=True)
	metric = models.CharField(max_length=128)
	submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
