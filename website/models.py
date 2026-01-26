from django.db import models
# from tinymce.models import HTMLField
from django_ace import AceWidget
import os
import uuid

class Website(models.Model):
    key      = models.CharField(max_length=255,unique=True,blank=True,null=True)
    title    = models.CharField(max_length=255,blank=True,null=True)
    base_header = models.TextField(
        blank=True,
        null=True,
        default=""
    )
    base_footer  = models.TextField(
        blank=True,
        null=True,
        default=""
    )
    fav_icon = models.FileField("website/favicon/",blank=True,null=True)
    def __str__(self):
        return self.key

class Page(models.Model):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, blank=True, null=True)
    key = models.CharField(max_length=255, unique=True, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    head = models.TextField(blank=True, null=True)
    header = models.ForeignKey('Widget',blank=True,null=True,on_delete=models.CASCADE,related_name="header_widget")
    body = models.TextField(blank=True, null=True)
    pre_process = models.TextField(
        blank=True,null=True,
    )
    footer = models.ForeignKey('Widget',blank=True,null=True,on_delete=models.CASCADE,related_name="footer_widget")
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    custom_css = models.TextField(blank=True, null=True)
    custom_js = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class Widget(models.Model):
    key = models.CharField(max_length=255,unique=True,blank=True,null=True)
    title = models.CharField(max_length=255,blank=True,null=True)
    content = models.TextField(blank=True,null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.key

class CascadeStyle(models.Model):
    page = models.ForeignKey('Page', on_delete=models.CASCADE, blank=True, null=True)
    content = models.TextField(
        blank=True,
        null=True,
        default=""
    )


class JavaScript(models.Model):
    page = models.ForeignKey('Page', on_delete=models.CASCADE, blank=True, null=True)
    content = models.TextField(
        blank=True,
        null=True,
        default=""
    )

class Api(models.Model):
    METHODS     = (
        ('GET','GET'),
        ('POST','POST'),
        ('PUT','PUT'),
        ('DELETE','DELETE'),
    )
    key         = models.CharField(default=uuid.uuid4(),max_length=255, unique=True, blank=True, null=True)
    name        = models.CharField(max_length=255, blank=True, null=True)
    method      = models.CharField(default="POST",choices=METHODS, max_length=50)
    description = models.TextField(blank=True,null=True)
    serializers = models.ManyToManyField("JsonSerializer",blank=True)
    content     = models.TextField(
        default="response_data['message'] = 'Default API response!'\nresponse_data['status_code'] = 200",
    )
    version     = models.DecimalField(default=0.1,max_digits=10,decimal_places=1)

    def __str__(self):
        return self.name

class JsonSerializer(models.Model):
    title   = models.CharField('Enter Class Name',max_length=255, unique=True, blank=True, null=True)
    key     = models.CharField(default=uuid.uuid4(),max_length=255, unique=True, blank=True, null=True)
    content = models.TextField(
        blank=True,
        null=True,
        default=""
    )
    depends_on = models.ManyToManyField("JsonSerializer",blank=True)

    def __str__(self):
        return self.title


def file_upload_path(instance, filename):
    return os.path.join("website/files/", filename)

class File(models.Model):
    data = models.FileField(upload_to=file_upload_path, blank=True, null=True)

    def update_file(self, new_file):
        if self.data:
            self.data.storage.delete(self.data.name)
        self.data.save(new_file.name, new_file, save=True)

    def __str__(self):
        return self.data.url
