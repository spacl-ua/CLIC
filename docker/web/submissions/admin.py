from django.contrib import admin
from . import models

class SubmissionAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Task)
admin.site.register(models.Phase)
admin.site.register(models.DockerImage)
