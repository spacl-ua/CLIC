from django.db import models
from django.utils import timezone


class Schedule(models.Model):
	name = models.CharField(max_length=32,
		help_text='A short name used to identify the schedule')


class Entry(models.Model):
	class Meta:
		ordering = ['datetime']

	schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
	datetime = models.DateTimeField()
	custom = models.CharField(max_length=256, blank=True)
	description = models.CharField(max_length=256)

	def passed(self):
		return self.datetime < timezone.now()
