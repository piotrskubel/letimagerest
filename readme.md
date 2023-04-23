# About project

Let Image Rest is a REST Framework browsable API example.
It was designed to serve both: anonymous and authenticated users.
One can upload image files and interact with them.
There are also several limitations and conveniencies, which can be customised.

# Setting the secrets

First of all you need to set your secret key and/or other sensitive data.
Open the .env file in the main directory and add proper variables.

.env:
```
SECRET_KEY={set your secret key here}
```

settings.py:
```
from decouple import config

...

SECRET_KEY = config('SECRET_KEY')
```
# Using database

With database set (by default sqlite3) you should make migrations, create superuser and run the server.
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Then enter:
```
http://127.0.0.1:8000/admin
```
and log with proper username and password.

# Registration and user activation

Unauthenticated users will be redirected to the anonymous view.
In such view there is a possibility to register a new account.
Such accounts will not be active immediately after the registration process.
You can change that in views.py:
```
class SignUpView(RegisterView):

...

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        #here you can specify, if user should be activated by admin
        user.is_active = False
        user.save()
```
To activate an user, log to the admin panel, click on the user and check 'active' box.

# Anonymous view

In the anonymous view all the images uploaded by any user will be resized to 720p resolution.
There is no possibility to access source image, which is a 'penalty' here.
Moreover you can specify a limit of the image files uploaded by such users (cumulatively).
You can do so in views.py:
```
class ViewOrUploadImagesAnonymously(viewsets.ModelViewSet):

...

    def get_queryset(self):
        #set maximum image files number, which can be uploaded anonymously
        #after reaching the limit oldest file will be deleted
        if UploadImageAnonymously.objects.all().count() > 5:
            UploadImageAnonymously.objects.first().delete()
        return UploadImageAnonymously.objects.all()
```
In the example above after uploading a new image by any user the oldest image 
will be automaticaly deleted, when the number of images is greater than 5.

#Authenticated view

In the authenticated view there are seperate upload directories for each user.
By default there is storage limit for such folders.
You can modify it in views.py:
```
class ViewOrUploadImages(viewsets.ModelViewSet):

...

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
```
Authenticated users can access source images files (full resolution), list and delete them.
Each object is listed with details url and it is possible to access object instance fast by clicking it.
User can also set expiration time in seconds during an image upload. 
Leaving such field blank will not trigger expiration at all.