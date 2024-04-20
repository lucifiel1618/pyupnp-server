from pathlib import Path
import xml.etree.cElementTree as ElementTree

from django.conf import settings
from django.http import HttpRequest, HttpResponse, FileResponse
from django.utils.html import escape
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from . import models
from . import services


def file_view(request: HttpRequest, path: str) -> FileResponse:
    f = Path(settings.MEDIA_ROOT, path)
    return FileResponse(f.open('rb'))


def device_detail(request: HttpRequest, device_id: int) -> HttpResponse:
    try:
        device = models.Device.objects.get(deviceId=device_id)
    except models.Device.DoesNotExist:
        meta = request.META
        netloc = f'{meta["REMOTE_ADDR"]}:{meta["SERVER_PORT"]}'
        path = meta['PATH_INFO']
        device = models.Device.objects.create(deviceId=device_id)
        services.initialize_device(device, netloc, path)

    return render(
        request,
        'device_detail.xml',
        {
            'device_detail': services.get_device_detail(device),
            'service_details': services.get_all_service_details(device)
        },
        content_type='text/xml'
    )


def service_detail(request: HttpRequest, device_id: int, service_id: int) -> HttpResponse:
    service = models.Service.objects.get(device__deviceId=device_id, id=service_id + 1)
    return render(
        request,
        'service_detail.xml',
        {
            'action_argumentlist_pairs': services.get_all_action_arugmentlist_pairs(service),
            'statevar_allowedvaluelist_pairs': services.get_all_statevar_allowedvaluelist_pairs(service)
        },
        content_type='text/xml'
    )


@csrf_exempt
def service_control(request: HttpRequest, device_id: int, service_id: int) -> HttpResponse:
    service = models.Service.objects.get(device__deviceId=device_id, id=service_id + 1)
    action_name = request.headers['SOAPAction'].rsplit('#', 1)[-1][:-1]
    action = service.action_set.get(name=action_name)
    host = request.get_host()
    arg_elements = ElementTree.fromstring(request.body).find(
        f'./envelope:Body/service_type:{action_name}',
        {'envelope': 'http://schemas.xmlsoap.org/soap/envelope/', 'service_type': service.serviceType}
    )
    args_in = {e.tag: action.argument_set.get(name=e.tag).parse(e.text) for e in arg_elements}
    if action_name == 'Browse':
        args_out = services.control_browse(**args_in, dir_as_item=True, base_url=host)
        items_xml = render_to_string(
            'action_response.xml',
            {
                'action_response_items': escape(render_to_string('action_response_items.xml', args_out)),
                **args_out
            }
        )
        print(f'{items_xml=}')
        return render(
            request, 'action.xml', {'action': action, 'action_response': items_xml}, content_type='text/xml'
        )
    raise NotImplementedError(f'Unknown Action: {action_name}. Possibly not yet implemented.')


@csrf_exempt
def service_event(request: HttpRequest, device_id: int, service_id: int) -> HttpResponse:
    raise NotImplementedError