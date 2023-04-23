from django.contrib import admin
from .models import UploadImageAuth, UploadImageAnonymously

admin.site.register(UploadImageAuth)
admin.site.register(UploadImageAnonymously)

