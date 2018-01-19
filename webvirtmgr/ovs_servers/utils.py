"""
Utilities.
"""

from subprocess import PIPE
from subprocess import Popen
from uuid import UUID


requires_bridge_set = [
    'mirrors',
    'netflow',
    'sflow',
    'ipfix',
    'stp_enable',
    'protocols',
    'flow_tables',
    'fail_mode',
    'status'
]

# other_config
requires_bridge_other_set = [
    'stp', 'stp-priority', 'stp-path-cost', 'stp-system-id',
    'stp-hello-time', 'stp-max-age', 'stp-forward-delay',

    'mcast-snooping-aging-time', 'mcast-snooping-table-size',
    'mcast-snooping-disable-flood-unregistered',

    'rstp-address', 'rstp-priority', 'rstp-ageing-time',
    'rstp-force-protocol-version', 'rstp-max-age',
    'rstp-forward-delay', 'rstp-transmit-hold-count'
]

requires_port_set = [
    'stp-path-cost',
    'mcast-snooping-flood', 'mcast-snooping-flood-reports',

    'rstp-enable', 'rstp-port-priority', 'rstp-port-num', 'rstp-path-cost',
    'rstp-port-admin-edge', 'rstp-port-auto-edge', 'rstp-admin-p2p-mac',
    'rstp-admin-port-state', 'rstp-port-mcheck'
]


def run(args):
    """
    Wrapper of 'subprocess.run'.

    :param args: Command arguments to execute.
    :return: instance of 'subprocess.Popen'.
    """
    popen = Popen(args, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    popen.wait()

    return popen


def is_valid_uuid(uuid):
    """
    Returns `True` if the given `uuid` is valid, otherwise returns `False`.

    :param uuid: str type value to be validated.
    :return: `True` if valid, else `False`.
    """
    try:
        UUID(uuid)
    except ValueError:
        return False
    return True


