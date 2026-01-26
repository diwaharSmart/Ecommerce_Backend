from django.contrib import admin
from django.urls import path
from website.views import *

urlpatterns = [
    path("",index,name="index"),
    path("web/<str:key>", PageView , name="page"),
    path("web/api/", ApiRequest.as_view(), name="api"),
]
