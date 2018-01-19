from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django import forms

from django.apps import apps
from .connection import Ovs_Server, parser_new, requires_bridge_other_set, requires_bridge_set

Ovs_Compute = apps.get_model('ovs_servers', 'Ovs_Compute')


def ovs_infrastructure(request):
    """
    Infrastructure page.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    errors = []
    srvs = {}
    srv_infos = {}

    try:
        managers = Ovs_Compute.objects.filter(active__exact=True)

        for index, manager in enumerate(managers, start=0):
            srvs[manager.name] = Ovs_Server(manager.name, manager.protocol, manager.ip_address, manager.port)
            srv_infos[manager.name] = srvs[manager.name].ovs_command(command='show', parser=parser_new)

        if request.method == 'POST':
            if 'init_manager' in request.POST:
                srv_name = request.POST.get('manager_for_init_reset', '')
                if srv_name:
                    srvs[srv_name].ovs_init()
                return HttpResponseRedirect(request.get_full_path())

            if 'reset_manager' in request.POST:
                srv_name = request.POST.get('manager_for_init_reset', '')
                if srv_name:
                    srvs[srv_name].ovs_emer_reset()
                return HttpResponseRedirect(request.get_full_path())
    except Exception as err:
        errors.append(err)

    return render(request, 'ovs_infrastructure.html', locals())


def ovs_manager(request, srv_name):
    """
    ovs_manager.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    errors = []
    ports = {}
    bridges_set = {}
    srv_name = srv_name

    try:
        manager = Ovs_Compute.objects.get(name__exact=srv_name)
        srv = Ovs_Server(manager.name, manager.protocol, manager.ip_address, manager.port)
        info = srv.ovs_command(command='show', parser=parser_new)
        bridges = sorted(info['Bridges'])

        for bridge in bridges:
            ports[bridge] = ",".join(info[bridge]['ports'])
            bridges_set[bridge] = srv.ovs_get_args_br(bridge, requires_bridge_set)
            bridges_set[bridge].update(srv.ovs_get_args_br(bridge, requires_bridge_other_set))
            bridges_set[bridge].update(srv.ovs_list_ifaces(bridge))

        if request.method == 'POST':
            if 'create' in request.POST:
                br_name = request.POST.get('name', '')
                srv.ovs_add_br(br_name)
                return HttpResponseRedirect(request.get_full_path())
            elif 'set_man' in request.POST:
                com = request.POST.get('man_command', '')
                if com:
                    srv.ovs_command(com)
                else:
                    raise Exception('Command is absent')
                return HttpResponseRedirect(request.get_full_path())
            elif 'delete_bridge' in request.POST:
                br_name = request.POST.get('bridge_for_del', '')
                srv.ovs_del_br(br_name)
                return HttpResponseRedirect(request.get_full_path())

    except Exception as err:
        errors.append(err)

    return render(request, 'ovs_manager.html', locals())


def bridge_manager(request, srv_name, bridge_name):
    """
    bridge_manager.
    """
    errors = []
    ports = {}
    port_sets = {}
    bridges_set = {}
    bridge_name = bridge_name

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    try:
        manager = Ovs_Compute.objects.get(name__exact=srv_name)
        srv = Ovs_Server(manager.name, manager.protocol, manager.ip_address, manager.port)

        bridge = srv.ovs_command(command='show', parser=parser_new)[bridge_name]
        ports = sorted(bridge['ports'])
        for port in ports:
            port_sets[port] = srv.ovs_get_args_port(port)
            port_sets[port].update(srv.ovs_list_port(port))
        ifaces = sorted(bridge['Interfaces'])
        bridges_set = srv.ovs_get_args_br(bridge_name, requires_bridge_set)
        bridges_set.update(srv.ovs_get_args_br(bridge_name, requires_bridge_other_set))

        stp = bridges_set.get('stp', False)
        stp_priority = bridges_set.get('stp-priority', 32768)
        stp_path_cost = bridges_set.get('stp-path-cost', 10)

        fail_mode = bridges_set.get('fail_mode', 'standalone')

        mcast_snooping_aging_time = bridges_set.get('mcast-snooping-aging-time', 300)
        mcast_snooping_table_size = bridges_set.get('mcast-snooping-table-size', 2048)
        mcast_snooping_disable_flood_unregistered = bridges_set.get('mcast-snooping-disable-flood-unregistered', False)
        mcast_snooping_flood = bridges_set.get('mcast-snooping-flood', False)
        mcast_snooping_flood_reports = bridges_set.get('mcast-snooping-flood-reports', False)

        rstp_address = bridges_set.get('rstp-address', "00:aa:aa:aa:aa:aa")
        rstp_priority = bridges_set.get('rstp-priority', 32768)
        rstp_ageing_time = bridges_set.get('rstp-ageing-time', 300)
        rstp_force_protocol_version = bridges_set.get('rstp-force-protocol-version', 2)
        rstp_max_age = bridges_set.get('rstp-max-age', 20)
        rstp_forward_delay = bridges_set.get('rstp-forward-delay', 15)
        rstp_transmit_hold_count = bridges_set.get('rstp-transmit-hold-count', 6)

        protocols = bridges_set.get('protocols', 'OpenFlow13')

        if request.method == 'POST':
            if 'delete_port' in request.POST:
                port_name = request.POST.get('port_for_del', '')
                srv.ovs_del_port(bridge_name, port_name)
                return HttpResponseRedirect(request.get_full_path())
            elif 'set_man' in request.POST:
                com = request.POST.get('man_command', '')
                if com:
                    srv.ovs_command(com)
                else:
                    raise Exception('Command is absent')
                return HttpResponseRedirect(request.get_full_path())
            elif 'create_port' in request.POST:
                args = {}
                port_name = request.POST.get('port_name', '')
                args['iface'] = request.POST.get('port_interface', '')
                args['tags'] = request.POST.get('port_tags', '')
                args['trunks'] = request.POST.get('trunks', '')
                srv.ovs_add_port(bridge_name, port_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'create_bond' in request.POST:
                args = {}
                port_name = request.POST.get('bond_name', '')
                args['iface_1'] = request.POST.get('iface_1', '')
                args['iface_2'] = request.POST.get('iface_2', '')
                args['tags'] = request.POST.get('port_tags', '')
                args['trunks'] = request.POST.get('trunks', '')
                args['lacp'] = request.POST.get('lacp', '')
                srv.ovs_add_bond(bridge_name, port_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_port' in request.POST:
                port_name = request.POST.get('port_name', '')
                args = {}
                srv.ovs_edit_port(port_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'stp_disable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'rstp_enable': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'stp_enable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'rstp_enable': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_bridge_base' in request.POST:
                args = {}
                val = request.POST.get('fail-mode', 'standalone')
                if fail_mode != val:
                    args['fail-mode'] = val
                if args:
                    srv.ovs_edit_br(bridge_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_bridge_stp' in request.POST:
                args = {}
                val = request.POST.get('stp-priority', 0)
                if stp_priority != val:
                    args['rstp-port-priority'] = val
                val = request.POST.get('stp-path-cost', 0)
                if stp_path_cost != val:
                    args['rstp-port-priority'] = val
                if args:
                    srv.ovs_edit_br(bridge_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_bridge_rstp' in request.POST:
                args = {}
                val = request.POST.get('rstp-address', "00:aa:aa:aa:aa:aa")
                if rstp_address != val:
                    args['rstp-address'] = val
                val = request.POST.get('rstp-priority', 32768)
                if rstp_priority != val:
                    args['rstp-priority'] = val
                val = request.POST.get('rstp-ageing-time', 300)
                if rstp_ageing_time != val:
                    args['rstp-ageing-time'] = val
                val = request.POST.get('rstp-force-protocol-version', 2)
                if rstp_force_protocol_version != val:
                    args['rstp-force-protocol-version'] = val
                val = request.POST.get('rstp-max-age', 20)
                if rstp_max_age != val:
                    args['rstp-max-age'] = val
                val = request.POST.get('rstp-forward-delay', 15)
                if rstp_forward_delay != val:
                    args['rstp-forward-delay'] = val
                val = request.POST.get('rstp-transmit-hold-count', 6)
                if rstp_transmit_hold_count != val:
                    args['rstp-transmit-hold-count'] = val

                if args:
                    srv.ovs_edit_br(bridge_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_bridge_flows' in request.POST:
                args = {}
                val = request.POST.get('protocols', 0)
                if stp_priority != val:
                    args['protocols'] = val
                if args:
                    srv.ovs_edit_br(bridge_name, args)
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-disable-flood_disable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-disable-flood': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-disable-flood_enable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-disable-flood': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-flood_disable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-flood': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-flood_enable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-flood': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-flood-reports_disable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-flood-reports': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast-snooping-flood-reports_enable' in request.POST:
                srv.ovs_edit_br(bridge_name, {'mcast-snooping-flood-reports': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_bridge_mcast' in request.POST:
                args = {}
                val = request.POST.get('mcast-snooping-aging-time', 300)
                if mcast_snooping_aging_time != val:
                    args['mcast-snooping-aging-time'] = val
                val = request.POST.get('mcast-snooping-table-size', 2048)
                if mcast_snooping_table_size != val:
                    args['mcast-snooping-table-size'] = val
                val = request.POST.get('', 0)
                if stp_priority != val:
                    args[''] = val
                val = request.POST.get('', 0)
                if stp_priority != val:
                    args[''] = val
                val = request.POST.get('', 0)
                if stp_priority != val:
                    args[''] = val
                val = request.POST.get('', 0)
                if stp_priority != val:
                    args[''] = val
                val = request.POST.get('', 0)
                if stp_priority != val:
                    args[''] = val

                if args:
                    srv.ovs_edit_br(bridge_name, args)
                return HttpResponseRedirect(request.get_full_path())

    except Exception as err:
        errors.append(err)

    return render(request, 'bridge_manager.html', locals())


def port_manager(request, srv_name, bridge_name, port_name):
    """
    port_manager.
    """
    errors = []
    ports = {}
    port_sets = {}
    bridge_name = bridge_name
    port_name = port_name

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))

    try:
        manager = Ovs_Compute.objects.get(name__exact=srv_name)
        srv = Ovs_Server(manager.name, manager.protocol, manager.ip_address, manager.port)

        port_sets = srv.ovs_get_args_port(port_name)
        port_sets.update(srv.ovs_list_port(port_name))
        tag = port_sets.get('tag', 0)
        trunks = str(port_sets.get('trunks', ''))
        lacp = str(port_sets.get('lacp', ''))
        stp_path_cost = port_sets.get('stp-path-cost', 0)

        mcast_snooping_flood_reports = port_sets.get('mcast-snooping-flood-reports', "")
        mcast_snooping_flood = port_sets.get('mcast-snooping-flood', "")

        rstp_enable = port_sets.get('rstp-enable', "")
        rstp_port_priority = port_sets.get('rstp-port-priority', 128)
        rstp_port_num = port_sets.get('rstp-port-num', 0)
        rstp_path_cost = port_sets.get('rstp-path-cost', 0)
        rstp_port_admin_edge = port_sets.get('rstp-port-admin-edge', "")
        rstp_port_auto_edge = port_sets.get('rstp-port-auto-edge', "")
        rstp_admin_port_state = port_sets.get('rstp-admin-port-state', "")
        rstp_port_mcheck = port_sets.get('rstp-port-mcheck', "")
        rstp_admin_p2p_mac = port_sets.get('rstp-admin-p2p-mac', 1)

        if request.method == 'POST':
            if 'edit_port_base' in request.POST:
                val = request.POST.get('trunks', '').replace(' ', '')
                if trunks != val:
                    srv.ovs_edit_port_noother(port_name, {'trunks': val})
                val = request.POST.get('tag', 0)
                if tag != val:
                    srv.ovs_edit_port(port_name, {'tag': val})
            elif 'set_man' in request.POST:
                com = request.POST.get('man_command', '')
                if com:
                    srv.ovs_command(com)
                else:
                    raise Exception('Command is absent')
            elif 'edit_port_stp' in request.POST:
                val = request.POST.get('stp-path-cost', 0)
                if stp_path_cost != val:
                    srv.ovs_edit_port(port_name, {'stp-path-cost': val})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-enable': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-enable': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_admin_adge_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-admin-edge': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_admin_adge_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-admin-edge': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_auto_adge_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-auto-edge': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_auto_adge_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-auto-edge': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_admin_port_state_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-admin-port-state': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_admin_port_state_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-admin-port-state': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_mcheck_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-mcheck': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'rstp_port_mcheck_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'rstp-port-mcheck': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast_snooping_flood_reports_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'mcast-snooping-flood-reports': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast_snooping_flood_reports_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'mcast-snooping-flood-reports': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast_snooping_flood_disable' in request.POST:
                srv.ovs_edit_port(port_name, {'mcast-snooping-flood': False})
                return HttpResponseRedirect(request.get_full_path())
            elif 'mcast_snooping_flood_enable' in request.POST:
                srv.ovs_edit_port(port_name, {'mcast-snooping-flood': True})
                return HttpResponseRedirect(request.get_full_path())
            elif 'edit_port_rstp' in request.POST:
                args = {}
                val = request.POST.get('rstp-port-priority', 0)
                if rstp_port_priority != val:
                    args['rstp-port-priority'] = val
                val = request.POST.get('rstp-port-num', 0)
                if rstp_port_num != val:
                    args['rstp-port-num'] = val
                val = request.POST.get('rstp-path-cost', 0)
                if rstp_path_cost != val:
                    args['rstp-path-cost'] = val
                val = request.POST.get('rstp-admin-p2p-mac', 0)
                if rstp_path_cost != val:
                    args['rstp-admin-p2p-mac'] = val
                if args:
                    srv.ovs_edit_port(port_name, args)
                return HttpResponseRedirect(request.get_full_path())
    except Exception as err:
        errors.append(err)

    return render(request, 'port_manager.html', locals())
