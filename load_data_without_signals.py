import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.core.management import call_command
from unittest.mock import patch

def main():
    print("Flushing database...")
    call_command('flush', interactive=False)
    
    print("Loading data while mocking post_save and pre_save signals...")
    with patch('django.db.models.signals.post_save.send'), \
         patch('django.db.models.signals.pre_save.send'), \
         patch('django.db.models.signals.post_delete.send'), \
         patch('django.db.models.signals.pre_delete.send'), \
         patch('django.db.models.signals.m2m_changed.send'):
        call_command('loaddata', 'datadump_utf8.json')
        
    print("Data loaded successfully.")

if __name__ == '__main__':
    main()
