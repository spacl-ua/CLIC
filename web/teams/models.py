from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import ugettext_lazy as _
from django.db import models


class TeamManager(UserManager):
	def get_by_natural_key(self, username):
		case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
		return self.get(**{case_insensitive_username_field: username})


class Team(AbstractUser):
	objects = TeamManager()
	email = models.EmailField(_('Email address'), blank=False, unique=True)
	affiliation = models.CharField(_('Affiliation'), blank=True, max_length=256,
		help_text=_('Your university, company or other affiliated institution (optional)'))
	members = models.CharField(_('Members'), blank=True, max_length=1024,
		help_text=_('Name of the members in your team, separated by comma (optional)'))

	def __str__(self):
		return self.username
