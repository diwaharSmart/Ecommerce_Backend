import os
import django
from django.core.management import call_command
from io import StringIO
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def main():
    apps = ['auth', 'ecommerce_app', 'website', 'admin', 'contenttypes', 'sessions', 'authtoken']
    out = StringIO()
    call_command('sqlsequencereset', *apps, stdout=out)
    sql = out.getvalue()
    
    if sql.strip():
        with connection.cursor() as cursor:
            cursor.execute(sql)
        print("Successfully reset PostgreSQL sequences for all apps.")
    else:
        print("No sequences needed resetting.")

if __name__ == '__main__':
    main()
