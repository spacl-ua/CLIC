from django.contrib import admin
from . import models

class SubmissionAdmin(admin.ModelAdmin):
    pass


class PhaseAdmin(admin.ModelAdmin):
    list_display = ('task', 'name', 'active')


admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Task)
admin.site.register(models.Phase, PhaseAdmin)
admin.site.register(models.DockerImage)