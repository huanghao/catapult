from django.shortcuts import render
from django.http import HttpResponse

import fab

def index(request):
    return render(request, 'index.html')

def poll(request):
    return HttpResponse(fab.run_test())

def term(requeset):
    return HttpResponse(fab.term())
