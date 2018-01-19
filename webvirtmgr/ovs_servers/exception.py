class OFCtlCmdExecError(Exception):
    """
    Raised when 'ovs-ofctl' command returns non-zero exit code.
    """


class OFCtlCmdParseError(Exception):
    """
    Raised when user specified parser fails to parse the outputs of
    'ovs-ofctl' command.
    """


class VSCtlCmdExecError(Exception):
    """
    Raised when 'ovs-vsctl' command returns non-zero exit code.
    """


class VSCtlCmdParseError(Exception):
    """
    Raised when user specified parser fails to parse the outputs of
    'ovs-vsctl' command.
    """