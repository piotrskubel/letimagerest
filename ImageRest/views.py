'''REST Framework views'''
import os
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from dj_rest_auth.registration.views import RegisterView
from django.conf import settings
from django.db.models import F, ExpressionWrapper, DurationField
from django.shortcuts import redirect
from django.urls import reverse
from .models import UploadImageAuth, UploadImageAnonymously
from .serializers import UploadImageSerializer, UploadImageAnonymouslySerializer, SignUpSerializer

class SignUpView(RegisterView):
    '''Fill in your data and wait for admin activation'''

    serializer_class = SignUpSerializer
    def perform_create(self, serializer):
        user = serializer.save(self.request)
        #here you can specify, if user should be activated by admin
        user.is_active = False
        user.save()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            #registration view is only accessible when not authenticated
            url = reverse('authenticated-list')
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)
def get_user_storage(owner_pk):
    '''Method responsible for calculating each auth user directory size'''
    user_directory = os.path.join(settings.MEDIA_ROOT, str(owner_pk))
    total_size = 0
    for dirpath, _, filenames in os.walk(user_directory):
        for names in filenames:
            paths = os.path.join(dirpath, names)
            total_size += os.path.getsize(paths)
    return total_size

@permission_classes([IsAuthenticated])
class ViewOrUploadImages(viewsets.ModelViewSet):
    '''Class representing browsable API view for authenticated users'''

    def get_queryset(self):
        #will be used, when expiry date is not null
        UploadImageAuth.objects.annotate(
            difference=ExpressionWrapper(
            datetime.now() - F('creation_date'), output_field=DurationField())).filter(
            expires_after__lte=F('difference')).delete()
        return UploadImageAuth.objects.filter(owner=self.request.user)
    def get_serializer_class(self):
        return UploadImageSerializer
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            url = reverse('anonymous-list')
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)
    def create(self, request, *args, **kwargs):
        owner_pk = request.user.pk
        uploaded_file = request.FILES['image_url']
        uploaded_file_size = uploaded_file.size
        #set storage limit per one authenticated user here
        MAXIMUM_ALLOWED_SIZE = 30 * 1024 * 1024
        if get_user_storage(owner_pk) + uploaded_file_size > MAXIMUM_ALLOWED_SIZE:
            return Response(
                {'error': 'Storage limit exceeded'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

class ViewOrUploadImagesAnonymously(viewsets.ModelViewSet):
    '''Class representing browsable API view for anonymous users'''

    #Use only, if you want to exclude DELETE method (recommended)
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    def get_queryset(self):
        #set maximum image files number, which can be uploaded anonymously
        #after reaching the limit oldest file will be deleted
        if UploadImageAnonymously.objects.all().count() > 5:
            UploadImageAnonymously.objects.first().delete()
        return UploadImageAnonymously.objects.all()

    def get_serializer_class(self):
        return UploadImageAnonymouslySerializer

    def create(self, request, *args, **kwargs):
        #refresh is needed to get updated image files list
        response = super().create(request, *args, **kwargs)
        response['Refresh'] = '0; url=/anonymous/'
        return response
    def list(self, request, *args, **kwargs):
        #replacing source file with resized file
        #resized image will be related to the object
        #source image will not be available to the users
        response = super().list(request, *args, **kwargs)
        for instance in self.get_queryset():
            source_path = instance.image_url.path
            dir_path = os.path.dirname(source_path)
            filename, extension = os.path.splitext(os.path.basename(source_path))
            resized_filename = f"{filename}-height_only-720x720-70{extension}"
            resized_path = os.path.join(dir_path, resized_filename)
            if os.path.exists(resized_path):
                os.remove(source_path)
                os.rename(resized_path,source_path)
        return response
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            url = reverse('authenticated-list')
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)
