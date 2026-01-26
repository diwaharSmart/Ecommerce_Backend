from django.shortcuts import render
from website.models import Page
from rest_framework.views import APIView
from rest_framework.response import Response
from website.models import Api
from rest_framework import status
from rest_framework import serializers
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
import sys
import os
from django.contrib import messages
import time
import requests
from django.core.cache import cache
# from Account.models import *
from django.db.models import Q
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token

# Create your views here.
def get_page(key):
    return Page.objects.get(key=key)

def index(request):
    data         = dict()
    try:
        data["page"] = get_page("index")
    except:
        data["page"] = get_page("404")
    return render(
        request,
        template_name="website/page.html",
        context=data
    )

def PageView(request,key):
    data         = dict()
    exec_globals = globals().copy()
    exec_globals.update({
        'render_data': data,
        'request': request,
    })
       
    try:
        if key == None:
            page         = get_page("index")
            data["page"] = page
        else:
            page         = get_page(key)
            data["page"] = page
        
        if page.pre_process not in ["",None]:
            exec(page.pre_process, exec_globals)
    except:
        data["page"] = get_page("404")
        
    return render(
        request,
        template_name="website/page.html",
        context=data
    )


def save_api_metrics(response_data, api_name, elapsed_time):
    try:
        api_metric = APIMetric(
            application_name=response_data.get('application_name', 'GAMEPLAY11'),
            vendor_name=response_data.get('vendor', 'INTERNAL'),
            api_name=api_name,
            request_packet=response_data.get('request_packet', ''),
            response_packet=response_data.get('response_packet', str(response_data)),
            status_code=response_data.get('status_code', 500),
            elapsed_time=elapsed_time,
            spi_status_code=response_data.get('spi_status_code', 'unknown'),
            error_message=response_data.get('error_message', ''),
            additional_info =response_data.get('message', '') 
        )
        api_metric.save()
    except Exception as e:
        # Log the exception if needed
        print(f"Error while saving API metrics: {e}")


class ApiRequest(APIView):

    def get_all_depended_serializer(self, obj, content):
        if obj.depends_on.exists():
            content = obj.content + "\n\n" + content
            for child_obj in obj.depends_on.all():
                content = self.get_all_depended_serializer(child_obj, content)
        else:
            content = obj.content + "\n\n" + content
        return content

    def process_request(self, request):
        response_data = {
            "request_packet": "",
            "response_packet": "",
            "api_status_code": "",
            "vendor": "INTERNAL",
            "application_name": "BotonAI",
        }
        try:
            api_key = request.data.get("api_key", None) or request.query_params.get("api_key", None)
        except:
            api_key = request.query_params.get("api_key", None)

        if not api_key:
            response_data['message'] = "API key is required"
            return Response({"error": "API key is required"}, status=status.HTTP_400_BAD_REQUEST)
        cache_key = f"key_{api_key}"
        cached_content = cache.get(cache_key)
        api_cache_key = f"api_name_{cache_key}"
        api_name = cache.get(api_cache_key)
        if cached_content:
            combined_content = cached_content
        else:
            try:
                api = Api.objects.get(key=api_key)
            except Api.DoesNotExist:
                response_data['message'] = "Invalid API key"
                return Response({"error": "Invalid API key"}, status=status.HTTP_400_BAD_REQUEST)

            api_name = api.name
            content = ""
            try:
                # Collect content from all connected serializers
                for json_serializer in api.serializers.all():
                    content = self.get_all_depended_serializer(json_serializer, content)
            except Exception as e:
                response_data['message'] = f"Error while collecting serializer content: {str(e)}"
                return Response({"error": f"Error while collecting serializer content: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            combined_content = content + "\n\n" + api.content
            cache.set(cache_key, combined_content, timeout=60 * 60 * 24)
            cache.set(api_cache_key, api_name, timeout=60 * 60 * 24)
            
        start_time = time.time()
        try:
            # Execute the combined content with access to all globals
            exec_globals = globals().copy()
            exec_globals.update({
                'response_data': response_data,
                'request': request,
                'serializers': serializers,  # Ensure the correct serializers module is used
            })
            exec(combined_content, exec_globals)
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_traceback = traceback.format_exc()
            error_line = error_traceback.splitlines()[-2]
            response_data['error_message'] = f"Line number [{error_line}] : Error while executing API content: {str(e)} \nTraceback :{error_traceback}"
            response_data['traceback'] = error_traceback
            response_data['error_line'] = error_line
            response_data['status_code'] = 500
            save_api_metrics(response_data, api_name, elapsed_time)
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elapsed_time = time.time() - start_time
        metrics_data = response_data.copy()
        
        status_code = response_data.get('status_code', 200)  # Default to 200 if status_code is not provided
        if not isinstance(status_code, int):
            status_code = 200
        response_data.pop('request_packet')
        response_data.pop('response_packet')
        response_data.pop('api_status_code')
        response_data.pop('vendor')
        response_data.pop('application_name')
        save_api_metrics(metrics_data, api_name, elapsed_time)
        return Response(response_data, status=status_code)

    def get(self, request, format=None, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, format=None, *args, **kwargs):
        return self.process_request(request)

    def put(self, request, format=None, *args, **kwargs):
        return self.process_request(request)

    def delete(self, request, format=None, *args, **kwargs):
        return self.process_request(request)




