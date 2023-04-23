"""LetImageRest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from ImageRest import views
from rest_framework import routers
from rest_framework.views import APIView

class Router(routers.DefaultRouter):
    '''Class representing default API router'''
    def get_api_root_view(self, *args, **kwargs):
        '''Method responsible for overriding API root view'''
        class UploadImages(APIView):
            '''Let Image Rest - Browsable API'''
            def get(self, request):
                '''Method responsible for viewing appropriate view'''
                if request.user.is_authenticated:
                    return redirect('authenticated/')
                else:
                    return redirect('anonymous/')
        return UploadImages.as_view()

router = Router()
router.register(r'anonymous', views.ViewOrUploadImagesAnonymously, basename='anonymous')
router.register(r'authenticated', views.ViewOrUploadImages, basename='authenticated')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('api-auth/', include('rest_framework.urls'))
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
