# forms.py
from django import forms
from django_ace import AceWidget
from .models import *

class ApiForm(forms.ModelForm):
    class Meta:
        model = Api
        fields = '__all__'
        widgets = {
            'content': AceWidget(
                mode='python',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
        }


class JsonSerializerForm(forms.ModelForm):
    class Meta:
        model = JsonSerializer
        fields = '__all__'
        widgets = {
            'content': AceWidget(
                mode='python',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
        }

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = '__all__'
        widgets = {
            'pre_process': AceWidget(
                mode='python',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
            'body': AceWidget(
                mode='html',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
            'custom_css': AceWidget(
                mode='css',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
            'custom_js': AceWidget(
                mode='js',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
        }

class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = '__all__'
        widgets = {
            'content': AceWidget(
                mode='html',
                theme='github',  # Choose a theme
                width='100%',
                height="500px",
                wordwrap=True,
                showinvisibles=False,
            ),
        }

class CssForm(forms.ModelForm):
    class Meta:
        model = Api
        fields = '__all__'
        widgets = {
            'content': AceWidget(
                mode='css',
                theme='github',  # Choose a theme
                width='100%',
                height="500px",
                wordwrap=True,
                showinvisibles=False,
            ),
        }

class JsForm(forms.ModelForm):
    class Meta:
        model = Api
        fields = '__all__'
        widgets = {
            'content': AceWidget(
                mode='js',
                theme='github',  # Choose a theme
                width='100%',
                height='500px',
                wordwrap=True,
                showinvisibles=False,
            ),
        }

