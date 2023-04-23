'''Serializers to be used within REST Framework'''
from io import BytesIO
from PIL import Image
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer
from versatileimagefield.datastructures import SizedImage
from versatileimagefield.registry import versatileimagefield_registry, AlreadyRegistered
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User
from .models import UploadImageAuth, UploadImageAnonymously

class HeightSizedImage(SizedImage):
    '''Class representing custom image resizer'''

    filename_key = 'height_only'
    def process_image(self, image, image_format, save_kwargs, width, height):
        '''Method responsible for calculating new width basing on height
        argument, resizing the image and returning new image file'''
        aspect_ratio = float(image.size[0]) / float(image.size[1])
        new_width = int(aspect_ratio * height)
        image = image.resize((new_width, height), resample=Image.ANTIALIAS)
        save_kwargs['format'] = image_format
        image_file = BytesIO()
        image.save(image_file, **save_kwargs)
        return image_file
try:
    versatileimagefield_registry.register_sizer('height_only', HeightSizedImage)
except AlreadyRegistered:
    pass

class SignUpSerializer(RegisterSerializer):
    '''Custom registration serializer'''

    email = None
    password1 = serializers.CharField(
        label='Password', write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(
        label='Repeat password', write_only=True, style={'input_type': 'password'})

class UserSerializer(serializers.ModelSerializer):
    '''User data serializer'''

    class Meta:
        '''Meta data'''
        model = User
        fields = ['username','id']

class CustomVersatileImageFieldSerializer(VersatileImageFieldSerializer):
    '''Custom image field serializer'''

    def to_representation(self, value):
        data = super().to_representation(value)
        #drop unused image sizes here
        data.pop('720p URL')
        return data

class UploadImageAnonymouslySerializer(serializers.ModelSerializer):
    '''Image files serializer (anonymous user)'''

    image_url = CustomVersatileImageFieldSerializer(
        #show or only create image files of sizes specified here
        sizes=[
        ('720p URL', 'height_only__720x720'),
        ('URL', 'url'),
        ]
    )
    class Meta:
        '''Meta data'''
        model = UploadImageAnonymously
        fields = ['image_url']

class UploadImageSerializer(serializers.ModelSerializer):
    '''Image files serializer (authenticated user)'''

    #allows to access instance view via direct link
    details = serializers.HyperlinkedIdentityField(view_name='authenticated-detail')
    image_url = VersatileImageFieldSerializer(
        sizes=[
        ('URL', 'url'),
        ]
    )
    class Meta:
        '''Meta data'''
        model = UploadImageAuth
        fields = ['details', 'owner', 'image_url', 'expires_after']

    def validate_image_url(self, value):
        '''Method responsible for limiting file size'''
        max_size = 8 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image file too large (maximum size is {max_size/(1024*1024)} MB)") 
        return value
