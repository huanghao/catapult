from django.db import models


class Proj(models.Model):

    name            = models.CharField(max_length=255, unique=True)
    home            = models.TextField()
    cvsmodel        = models.TextField()
    cvsuser         = models.TextField(blank=True)
    cvspass         = models.TextField(blank=True)
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

    name            = models.CharField(max_length=255, blank=True)
    model           = models.CharField(max_length=255, blank=True)
    description     = models.TextField(blank=True)
    manufacturer    = models.CharField(max_length=255, blank=True)
    product         = models.CharField(max_length=255, blank=True)
    serial          = models.CharField(max_length=255, blank=True)
    uuid            = models.CharField(max_length=255, blank=True)
    cpu             = models.CharField(max_length=255, blank=True)
    memory          = models.CharField(max_length=255, blank=True)
    disk            = models.CharField(max_length=255, blank=True)
    assetno         = models.CharField(max_length=255, blank=True)
    idc             = models.ForeignKey('Idc', blank=True)
    cabinet         = models.CharField(max_length=255, blank=True)
    position        = models.CharField(max_length=255, blank=True)
    ip              = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        if not self.name or self.name == self.ip:
            return self.ip
        return '%s(%s)' % (self.name, self.ip)
    
class Idc(models.Model):

    name = models.CharField(max_length=255, unique=True)
    cabinet = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.name
