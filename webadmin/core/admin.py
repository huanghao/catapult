from django.contrib import admin
from webadmin.core.models import Proj, Host, IDC, IP

admin.site.register([Proj, Host, IDC, IP])
