from django.db import models


class Ovs_Compute(models.Model):
    name = models.CharField(max_length=20)
    protocol_choices = (
        ('tcp', 'tcp'),
        ('ssl', 'ssl'),
    )
    protocol = models.CharField(max_length=3, default='tcp', choices=protocol_choices)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')
    port = models.CharField(default='6640', max_length=400,
                            help_text="(TCP or SSL) port number to connect.")
    state = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
