from django.db import models


class Proj(models.Model):

    name            = models.CharField(max_length=255, unique=True)
    home            = models.TextField()
    svn             = models.TextField()
    link_py_modules = models.TextField(blank=True)
    pre_setup       = models.TextField(blank=True)
    post_setup      = models.TextField(blank=True)
    pre_deploy      = models.TextField(blank=True)
    post_deploy     = models.TextField(blank=True)
    pre_rollback    = models.TextField(blank=True)
    post_rollback   = models.TextField(blank=True)
    hosts           = models.ManyToManyField('Host', blank=True)

    def __unicode__(self):
        return self.name


class Host(models.Model):

    name = models.CharField(max_length=255, unique=True)
    ip = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        if self.name == self.ip:
            return self.name
        return '%s(%s)' % (self.name, self.ip)
    
