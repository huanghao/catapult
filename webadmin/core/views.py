from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'index.html')

def poll(request):
    import fab
    return HttpResponse(fab.run_test())
