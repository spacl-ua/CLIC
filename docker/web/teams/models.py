from django.contrib.auth.models import AbstractUser


class Team(AbstractUser):
	def __str__(self):
		return self.username
