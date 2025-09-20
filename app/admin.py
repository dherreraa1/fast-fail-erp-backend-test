from django.contrib import admin
from .models import Company, Document, ValidationStep, ValidationAction

admin.site.register(Company)
admin.site.register(Document)
admin.site.register(ValidationStep)
admin.site.register(ValidationAction)
