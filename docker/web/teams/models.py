from django.contrib.auth.models import AbstractUser, UserManager


class TeamManager(UserManager):
	def get_by_natural_key(self, username):
		case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
		return self.get(**{case_insensitive_username_field: username})


class Team(AbstractUser):
	objects = TeamManager()
	def __str__(self):
		return self.username
