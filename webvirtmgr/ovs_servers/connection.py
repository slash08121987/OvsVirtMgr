from django.apps import apps
from .ctl import Ctl
from .parser import parser_other, parser_new, line_parser, show_cmd_parser, list_cmd_parser, parser_list_port
from .utils import requires_port_set, requires_bridge_set, requires_bridge_other_set

Ovs_Compute = apps.get_model('ovs_servers', 'Ovs_Compute')


class Ovs_Server():
    def __init__(self, name='local', protocol='tcp', ip_address='127.0.0.1', port=6640):
        self.name = name
        self.ctl_server = self._ctl_connect(protocol, ip_address, port)

    def _ctl_connect(self, protocol, ip_addr, port):
        try:
            return Ctl(protocol=protocol, ip_addr=ip_addr, port=port)
        except Exception as err:
            return err

    def ovs_command(self, command='show', parser=show_cmd_parser, table_format='list', data_format='string'):
        return self.ctl_server.run(command=command, parser=parser, table_format=table_format, data_format=data_format)

    def ovs_ofctl_command(self, command='show', parser=show_cmd_parser, table_format='list', data_format='string'):
        return self.ctl_server.ofctl_run(command=command, parser=parser, table_format=table_format, data_format=data_format)

    def ovs_list_br(self):
        return self.ovs_command(command='list-br', parser=line_parser)

    def ovs_add_br(self, br):
        com = 'add-br %s' % br
        return self.ovs_command(command=com, parser=line_parser)

    def ovs_br_ex(self, br):
        try:
            com = 'br-exists %s' % br
            self.ovs_command(command=com, parser=line_parser)
            return True
        except:
            return False

    def ovs_del_br(self, br):
        """
        Delete the bridge.
        """
        ex = self.ovs_br_ex(br)
        if ex:
            com = 'del-br %s' % br
            self.ovs_command(command=com, parser=line_parser)
            return True
        else:
            return False

    def ovs_get_args_br(self, br, args):
        """
        Get settings of the bridge.
        """
        answer = {}
        if self.ovs_br_ex(br):
            com = 'get Bridge %s ' % br
            for arg in args:
                if arg in requires_bridge_set:
                    ans = self.ovs_command(command=com + arg, parser=line_parser)[0]
                    if ans and ans not in ['false', '[]', '{}']:
                        answer[arg] = ans
                elif arg in requires_bridge_other_set:
                    ans = self.ovs_command(command=com + 'other-config', parser=parser_other)
                    for k, v in ans.items():
                        if v not in ['false', '[]', '{}']:
                            answer[k] = v
            return answer
        else:
            raise Exception("Bridge %s does not exist" % br)
            # answer['error'] = 'error'
            # return answer

    def ovs_edit_br(self, br, args):
        if self.ovs_br_ex(br):
            com = 'set Bridge %s ' % br
            for arg, value in args.items():
                if arg in requires_bridge_set:
                    setting = arg + '=' + str(value)
                    self.ovs_command(command=com + setting, parser=line_parser)
                elif arg in requires_bridge_other_set:
                    setting = arg + '=' + str(value)
                    self.ovs_command(command=com + 'other-config:' + setting, parser=line_parser)
            return True
        else:
            return False

    def ovs_list_ifaces(self, br):
        com = 'list-ifaces %s' % br
        return {'Interfaces': self.ovs_command(command=com, parser=line_parser)}

    def ovs_init(self):
        return self.ovs_command(command='init', parser=line_parser)

    def ovs_emer_reset(self):
        return self.ovs_command(command='emer-reset', parser=line_parser)

    def ovs_list_ports(self, br):
        com = 'list-ports %s' % br
        return self.ovs_command(command=com, parser=line_parser)

    def ovs_add_port(self, br, port, args):
        com = 'add-port %s %s' % (br, port)
        self.ovs_command(command=com, parser=line_parser)
        #raise Exception(br, port, args)
        if args['tags']:
            com = 'set Port %s %s=%s' % (port, "tag", args['tags'])
            self.ovs_command(command=com, parser=line_parser)
        if args['trunks']:
            com = 'set Port %s %s=%s' % (port, "trunks", args['trunks'])
            self.ovs_command(command=com, parser=line_parser)
        if args['iface']:
            com = 'set Interface %s type=%s' % (port, args['iface'])
            self.ovs_command(command=com, parser=line_parser)
        return True

    def ovs_add_bond(self, br, port, args):
        if args['iface_1'] and args['iface_2']:
            com = 'add-bond %s %s %s %s' % (br, port, args['iface_1'], args['iface_2'])
            self.ovs_command(command=com, parser=line_parser)
        else:
            raise Exception('Set both interfaces')

        if args['tags']:
            com = 'set Port %s %s=%s' % (port, "tag", args['tags'])
            self.ovs_command(command=com, parser=line_parser)
        if args['trunks']:
            com = 'set Port %s %s=%s' % (port, "trunks", args['trunks'])
            self.ovs_command(command=com, parser=line_parser)
        if args['lacp']:
            com = 'set Port %s %s=%s' % (port, "lacp", args['lacp'])
            self.ovs_command(command=com, parser=line_parser)
        return True

    def ovs_del_port(self, br, port):
        com = 'del-port %s %s' % (br, port)
        return self.ovs_command(command=com, parser=line_parser)

    def ovs_get_args_port(self, port):
        """
        Get settings of the port.
        """
        com = 'get Port %s %s' % (port, 'other-config')
        answer = {}
        ans = self.ovs_command(command=com, parser=parser_other)
        for k, v in ans.items():
            if v not in ['false', '[]', '{}']:
                answer[k] = v
        return answer

    def ovs_list_port(self, port):
        """
        Get settings of the port 2.
        """
        com = 'list port %s' % port
        return self.ovs_command(command=com, parser=parser_list_port)

    def ovs_edit_port(self, port, args):
        """
        Edit settings of the port.
        """
        com = 'set Port %s other-config:' % port

        for arg, value in args.items():
            if arg in requires_port_set:
                setting = arg + '=' + str(value)
                # raise Exception(com + setting)
                self.ovs_command(command=com + setting, parser=line_parser)

    def ovs_edit_port_noother(self, port, args):
        """
        Edit settings of the port.
        """
        com = 'set Port %s ' % port

        for arg, value in args.items():
            if arg in ['trunks']:
                setting = arg + '=' + str(value)
                # raise Exception(com + setting)
                # raise  Exception(com + setting)
                self.ovs_command(command=com + setting)

if '_name__' == '__main__':
    pass
    srv = Ovs_Server()
    port = 'vlan5'
    com = 'set Port %s other-config:trunks=[15, 17]' % port
    answer = srv.ovs_command(command=com, parser=parser_other())
    print(answer)


