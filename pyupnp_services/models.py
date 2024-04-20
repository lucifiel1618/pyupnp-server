import platform
from typing import Self
from django.db import models


class Device(models.Model):
    deviceId = models.IntegerField()
    deviceType = models.CharField(max_length=200, default='urn:schemas-upnp-org:device:MediaServer:1')
    friendlyName = models.CharField(max_length=200, default='Python Slideshow Server')
    manufacturer = models.CharField(max_length=200, default='python-slideshow')
    manufacturerURL = models.URLField(default='https://placeholder.com')
    modelDescription = models.CharField(
        max_length=200,
        default='{p.system}/{p.release}, UPnP/1.0, PyUPnPServer for UPnP devices/1.0'.format(p=platform.uname())
    )
    modelName = models.CharField(max_length=200, default='SlideShow')
    modelNumber = models.CharField(max_length=20, default='1.0.0')
    modelURL = models.URLField(default='https://placeholder.com')
    serialNumber = models.CharField(max_length=20, default='1.0.0')
    UDN = models.CharField(
        verbose_name='Unique Device Name', max_length=41,
        default='uuid:00000000-0000-0000-0000-000000000000'
    )
    UPC = models.CharField(verbose_name='Universal Product Code', max_length=50)
    presentationURL = models.URLField(default='https://placeholder.com')


class Service(models.Model):
    serviceType = models.CharField(max_length=200)
    serviceId = models.CharField(max_length=200)
    SCPDURL = models.URLField(verbose_name='Service Control Protocol Description URL')
    controlURL = models.URLField()
    eventSubURL = models.URLField()

    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    @classmethod
    def create(cls, service_name, version, *, device) -> Self:
        service = cls.objects.create(
            serviceType=f'urn:schemas-upnp-org:service:{service_name}:{version}',
            serviceId=f'urn:upnp-org:serviceId:{service_name}',
            device=device
        )
        subdomain = f'/dev{device.deviceId}/srv{service.id - 1}'
        service.SCPDURL = f'{subdomain}.xml'
        service.controlURL = f'{subdomain}/ctl'
        service.eventSubURL = f'{subdomain}/evt'
        service.save()
        return service


class Action(models.Model):
    name = models.CharField(max_length=100)

    service = models.ForeignKey(Service, on_delete=models.CASCADE)


class Argument(models.Model):
    name = models.CharField(max_length=100)
    direction = models.CharField(max_length=3, choices=[('in', 'in'), ('out', 'out')])
    relatedStateVariable = models.CharField(max_length=100)  # Assuming related state variable name is stored

    action = models.ForeignKey(Action, on_delete=models.CASCADE)

    def parse(self, value: str):
        statevar = self.action.service.statevariable_set.get(name=self.relatedStateVariable)
        if value in {'None', 'none', ''}:
            value = None
        if statevar.dataType in {'ui1', 'ui2', 'ui4', 'ui8', 'i1', 'i2', 'i4', 'i8', 'int'}:
            return int(value) if value is not None else 0
        if statevar.dataType in {'r4', 'r8', 'number', 'float'}:
            return float(value) if value is not None else 0.
        if statevar.dataType in {'boolean'}:
            return bool(value) if value is not None else False
        return value if value is not None else ''


class StateVariable(models.Model):
    name = models.CharField(max_length=100)
    dataType = models.CharField(max_length=20)
    sendEvents = models.CharField(max_length=3, default='no', choices=[('no', 'no'), ('yes', 'yes')])

    service = models.ForeignKey(Service, on_delete=models.CASCADE)


class AllowedValue(models.Model):
    allowedValue = models.CharField(max_length=100)

    stateVariable = models.ForeignKey(StateVariable, on_delete=models.CASCADE)
