from pagedown.widgets import AdminPagedownWidget
from django.db import models
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext_lazy as _

from .models import Entry, Schedule


class PagedownFlatpageAdmin(FlatPageAdmin):
	formfield_overrides = {
		models.TextField: {'widget': AdminPagedownWidget},
	}

	fieldsets = (
		(None, {
			'fields': ('url', 'title', 'content', 'sites')}),
		(_('Advanced options'), {
			'classes': ('collapse',),
			'fields': ('registration_required', 'template_name')}),
	)

	list_display = ('url', 'title')
	list_filter = ()


class EntryInline(admin.StackedInline):
	model = Entry
	extra = 1


class ScheduleAdmin(admin.ModelAdmin):
	list_display = ('id', 'name',)
	inlines = [EntryInline]


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, PagedownFlatpageAdmin)
admin.site.register(Schedule, ScheduleAdmin)
