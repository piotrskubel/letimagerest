'''Django models to be used within REST Framework'''
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from versatileimagefield.fields import VersatileImageField

class UploadImageAnonymously(models.Model):
    '''Model representing image files upload by anonymous user'''

    image_url = VersatileImageField(
    'Upload image', upload_to='anonymous', null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)

    def delete(self, *args, **kwargs):
        '''Method responsible for deleting images when the quota is reached'''
        storage, path = self.image_url.storage, self.image_url.path
        super().delete(*args,**kwargs)
        storage.delete(path)

def upload_path(instance, filename):
    '''Method creating custom path for each authenticated user'''
    owner_pk=instance.owner.pk
    return f'{owner_pk}/{filename}'

class UploadImageAuthQuerySet(models.QuerySet):
    '''Custom queryset for authenticated model'''

    def delete(self, *args, **kwargs):
        '''Method responsible for deleting images related to expired objects'''
        for obj in self:
            obj.image_url.delete(save=False)
        super().delete(*args, **kwargs)

class UploadImageAuth(models.Model):
    '''Model representing image files upload by authenticated user'''

    owner = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    image_url = VersatileImageField(
    'Upload image', upload_to=upload_path, null=True, blank=True)
    expires_after = models.DurationField('Expiry time in seconds (optional)',
        null=True, blank=True, validators=[MaxValueValidator(
        #you can set custom maximum expiry time here: days*hours*minutes*seconds
        timedelta(seconds=30*24*60*60))])
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    objects = UploadImageAuthQuerySet.as_manager()

    def delete(self, *args, **kwargs):
        '''Method responsible for deleting image files related to objects instances'''
        storage, path = self.image_url.storage, self.image_url.path
        super().delete(*args,**kwargs)
        storage.delete(path)
    