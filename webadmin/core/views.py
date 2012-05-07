from django.shortcuts import render
from django.http import HttpResponse

from fab import fab, stop

def index(request):
    return render(request, 'index.html')

def test(request):
    def gen():
        import time
        import random

        n = 20
        for i in range(n):
            yield '[%d] %f' % (i+1, random.random())
            if i < n-1:
                time.sleep(random.random()*.5+.5)
            
    return HttpResponse(gen())

def poll(request):
    #FIXME: user starting the web server(www) is not user running fabric(mc or myself)!
    return HttpResponse(fab())

def term(request):
    return HttpResponse(stop())
