from django.db import models


class Proj(models.Model):

    name            = models.CharField(max_length=255, unique=True)
    home            = models.CharField(max_length=255)
    owner           = models.CharField(max_length=255, default='mc')
    cvs_model       = models.CharField(max_length=255, default='svn')
    cvs_path        = models.TextField()
    cvs_user        = models.CharField(max_length=255, blank=True)
    cvs_pass        = models.CharField(max_length=255, blank=True)
    link_py_modules = models.TextField(blank=True)
    pre_setup       = models.TextField(blank=True)
    post_setup      = models.TextField(blank=True)
    pre_deploy      = models.TextField(blank=True)
    post_deploy     = models.TextField(blank=True)
    pre_rollback    = models.TextField(blank=True)
    post_rollback   = models.TextField(blank=True)
    ips             = models.ManyToManyField('IP', null=True, blank=True)

    def __unicode__(self):
        return self.name


class IP(models.Model):

    addr      = models.CharField(max_length=255, null=False, blank=False, unique=True)
    interface = models.CharField(max_length=255, null=False, blank=False)
    host      = models.ForeignKey('Host', null=True, blank=True)

    def __unicode__(self):
        return self.addr


class Host(models.Model):

    uuid            = models.CharField(max_length=255, null=False, blank=False, unique=True)
    name            = models.CharField(max_length=255, blank=True)
    model           = models.CharField(max_length=255, blank=True)
    manufacturer    = models.CharField(max_length=255, blank=True)
    product         = models.CharField(max_length=255, blank=True)
    serial          = models.CharField(max_length=255, blank=True)
    memory          = models.CharField(max_length=255, blank=True)
    cpu             = models.TextField(blank=True)
    disk            = models.CharField(max_length=255, blank=True)
    assetno         = models.CharField(max_length=255, blank=True)
    cabinet         = models.CharField(max_length=255, blank=True)
    position        = models.CharField(max_length=255, blank=True)
    description     = models.TextField(blank=True)
    idc             = models.ForeignKey('IDC', null=True, blank=True)

    def __unicode__(self):
        return self.uuid if not self.name else self.name

    
class IDC(models.Model):

    name    = models.CharField(max_length=255, unique=True)
    cabinet = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.name
