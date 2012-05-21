import os, sys, warnings

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(path, '..'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'webadmin.settings'
warnings.simplefilter('ignore', DeprecationWarning)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
