from django.contrib import admin
from . import models


class MeasurementInline(admin.StackedInline):
	model = models.Measurement
	extra = 1
	max_num = 10


class SubmissionAdmin(admin.ModelAdmin):
	list_display = ('id', 'team', 'phase', 'status', 'decoder_size', 'data_size', 'docker_image', 'timestamp',)
	inlines = [MeasurementInline]


class PhaseAdmin(admin.ModelAdmin):
	list_display = ('task', 'name', 'active', 'hidden', 'decoder_fixed', 'ask_permission', 'cpu', 'timeout', 'memory')


admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Task)
admin.site.register(models.Phase, PhaseAdmin)
admin.site.register(models.DockerImage)
