'''REST Framework tests'''
import io
import random
import os
from PIL import Image, ImageDraw
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

@pytest.fixture
def test_user():
    '''Method used to create user for testing purposes'''
    return User.objects.create_user(username='testuser', password='testpass')

@pytest.mark.django_db
def test_upload_image_anonymous(client):
    '''Method used to test image creation by anonymous user'''
    url = reverse('anonymous-list')
    img = io.BytesIO()
    image = Image.new('RGB', (100, 100))
    image.save(img, format='JPEG')
    img.seek(0)
    response = client.post(url, {'image_url': SimpleUploadedFile(
        't_e_s_t.jpg', img.getvalue())}, format='multipart')
    assert response.status_code == 201
    for root, _, files in os.walk(settings.MEDIA_ROOT):
        for file in files:
            if 't_e_s_t' in file:
                os.remove(os.path.join(root, file))

@pytest.mark.django_db
def test_upload_image_authenticated(client, test_user):
    '''Method used to test image creation by authenticated user'''
    client.login(username='testuser', password='testpass')
    url = reverse('authenticated-list')
    img = io.BytesIO()
    image = Image.new('RGB', (100, 100))
    image.save(img, format='JPEG')
    img.seek(0)
    response = client.post(url, {'image_url': SimpleUploadedFile(
        't_e_s_t.jpg', img.getvalue())}, format='multipart')
    assert response.status_code == 201
    for root, _, files in os.walk(settings.MEDIA_ROOT):
        for file in files:
            if 't_e_s_t' in file:
                os.remove(os.path.join(root, file))
  
@pytest.mark.django_db
def test_upload_large_image_authenticated(client, test_user):
    '''Method used to test too large image file blocking'''
    client.login(username='testuser', password='testpass')
    url = reverse('authenticated-list')
    img = io.BytesIO()
    image = Image.new('RGB', (15000, 15000))
    draw = ImageDraw.Draw(image)
    for i in range(100):
        x1 = random.randint(0, 15000)
        y1 = random.randint(0, 15000)
        x2 = random.randint(0, 15000)
        y2 = random.randint(0, 15000)
        color = (random.randint(0, 255),
            random.randint(0, 255), random.randint(0, 255))
        draw.rectangle([x1, y1, x2, y2], fill=color)
    image.save(img, format='JPEG')
    img.seek(0)
    response = client.post(url, {'image_url': SimpleUploadedFile(
        'test.jpg', img.getvalue())}, format='multipart')
    img_size = img.getbuffer().nbytes
    print(f"Image size: {img_size/(1024*1024)} MB")
    assert response.status_code == 400

@pytest.mark.django_db
def test_create_user(client):
    '''Method used to test registering new user'''
    url = reverse('register')
    data = {
        'username': 'newuser',
        'password1': 'newpwpw1',
        'password2': 'newpwpw1'
    }
    response = client.post(url, data)
    print(response.content)
    assert response.status_code == 204

@pytest.mark.django_db
def test_authenticated_url(client, test_user):
    '''Method used to check whether auth user can enter proper url'''
    client.login(username='testuser', password='testpass')
    response = client.get('/authenticated/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_anonymous_url(client):
    '''Method used to check whether anonym user can enter proper url'''
    response = client.get('/anonymous/')
    assert response.status_code == 200
