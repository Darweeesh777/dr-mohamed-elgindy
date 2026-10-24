from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('videos/', views.videos, name='videos'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('articles/', views.articles, name='articles'),
    path('articles/<int:pk>/', views.article_detail, name='article'),
]
