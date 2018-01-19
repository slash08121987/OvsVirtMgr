from ovs_vsctl import VSCtl, line_parser, list_cmd_parser, show_cmd_parser
from webvirtmgr.ovs_servers.ctl import Ctl
from webvirtmgr.ovs_servers.parser import parser_new
import ast, json
import re
vsctl = Ctl(protocol='tcp', ip_addr='127.0.0.1', port=6640)


def parser_list_port(buf):
    print(buf)
    ans = {}
    for s in buf.splitlines():
        key, value = s.replace(' ', '').replace(r'"', '').split(":")
        if '[' in value:
            value = value[1:len(value) - 1]
            pattern = re.compile('(set|map|uuid),(.*)')
            result = pattern.match(value)
            if result:
                val = result.groups()[1]
                if 'set' in value:
                    if val == '[]':
                        val = []
                    else:
                        val = [i for i in val[1:-1].split(',')]
            else:
                val = value
        else:
            val = value

        ans[key] = val
    return ans


command = 'list-ifaces br0'
parser = line_parser

records = vsctl.run(command=command, parser=parser)

print('after = ', records)

