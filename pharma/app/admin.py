from django.contrib import admin
from app import models

admin.site.register(models.Drug)
admin.site.register(models.DrugIllness)
admin.site.register(models.Illness)
