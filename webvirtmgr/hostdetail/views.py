from libvirt import libvirtError

from django.apps import apps
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse
import json
import time

Compute = apps.get_model('servers', 'Compute')
# from servers.models import Compute
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def hostusage(request, host_id):
    """
    Return Memory and CPU Usage
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    points = 5
    datasets = {}
    cookies = {}
    compute = Compute.objects.get(id=host_id)
    curent_time = time.strftime("%H:%M:%S")

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        cpu_usage = conn.get_cpu_usage()
        mem_usage = conn.get_memory_usage()
        conn.close()
    except libvirtError:
        cpu_usage = 0
        mem_usage = 0

    try:
        cookies['cpu'] = request.COOKIES.get('cpu')
        cookies['mem'] = request.COOKIES.get('mem')
        cookies['timer'] = request.COOKIES.get('timer')
    except KeyError:
        cookies['cpu'] = None
        cookies['mem'] = None

    if not cookies['cpu'] and not cookies['mem']:
        datasets['cpu'] = [23]
        datasets['mem'] = [21]
        datasets['timer'] = [curent_time]
    else:
        datasets['cpu'] = eval(cookies['cpu'])
        datasets['mem'] = eval(cookies['mem'])
        datasets['timer'] = eval(cookies['timer'])

    datasets['timer'].append(curent_time)
    datasets['cpu'].append(int(cpu_usage['usage']))
    #datasets['mem'].append(int(mem_usage['usage']) / 1048576)
    datasets['mem'].append(int(mem_usage['percent']))

    if len(datasets['timer']) > points:
        datasets['timer'].pop(0)
    if len(datasets['cpu']) > points:
        datasets['cpu'].pop(0)
    if len(datasets['mem']) > points:
        datasets['mem'].pop(0)

    cpu = {
        'labels': datasets['timer'],
        'datasets': [
            {
                "label": 'CPU usage',
                "fill": False,
                "borderColor": 'orange',
                "backgroundColor": 'orange',
                "fillColor": 'rgba(241,72,70,0.5)',
                "strokeColor": "rgba(241,72,70,1)",
                "pointColor": "rgba(241,72,70,1)",
                "pointStrokeColor": "#fff",
                "data": datasets['cpu']
            },
            {
                "label": "Memory usage",
                "fill": False,
                "borderColor": 'rgba(0,0,255,0.5)',
                "backgroundColor": 'rgba(0,0,255,0.5)',
                "fillColor": "rgba(0,0,255,0.5)",
                "strokeColor": "rgba(249,134,33,1)",
                "pointColor": "rgba(0,0,255,0.5)",
                "pointStrokeColor": "#fff",
                "data": datasets['mem']
            }
        ]
    }

    memory = {
        'labels': datasets['timer'],
        'datasets': [
            {
                "label": "Memory usage",
                "fill": True,
                "borderColor": 'rgba(0,0,255,0.5)',
                "backgroundColor": 'rgba(0,0,255,0.5)',
                "fillColor": "rgba(0,0,255,0.5)",
                "strokeColor": "rgba(249,134,33,1)",
                "pointColor": "rgba(249,134,33,1)",
                "pointStrokeColor": "#fff",
                "data": datasets['mem']
            }
        ]
    }

    data = json.dumps({'cpu': cpu, 'memory': memory})
    response = HttpResponse(content_type="text/javascript")
    response.set_cookie('cpu', datasets['cpu'])
    response.set_cookie('timer', datasets['timer'])
    response.set_cookie('mem', datasets['mem'])
    response.write(data)

    return response


def overview(request, host_id):
    """
    Overview page.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    errors = []
    time_refresh = TIME_JS_REFRESH

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        hostname, host_arch, host_memory, logical_cpu, model_cpu, uri_conn = conn.get_node_info()
        hypervisor = conn.hypervisor_type()
        mem_usage = conn.get_memory_usage()
        conn.close()
    except libvirtError as err:
        errors.append(err)

    return render_to_response('hostdetail.html', locals())
    # return render_to_response('hostdetail.html', locals(), context_instance=RequestContext(request))
    # return(request, 'hostdetail.html', locals())
