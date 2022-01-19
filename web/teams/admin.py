from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from . import forms, models


class TeamAdmin(UserAdmin):
	add_form = forms.TeamCreationForm
	form = forms.TeamChangeForm
	model = models.Team
	list_display = ['username', 'email', 'is_staff', 'is_active', 'paperid']

admin.site.register(models.Team, TeamAdmin)
