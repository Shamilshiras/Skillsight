"""
WSGI config for SkillSight project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillsight.settings')

application = get_wsgi_application()
