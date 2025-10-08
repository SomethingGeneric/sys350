"""
This module implements simple helper functions for managing service instance objects

Modified from: https://github.com/vmware/pyvmomi-community-samples
"""

# __author__ = "VMware, Inc."

import atexit
from pyVim.connect import SmartConnect, Disconnect

# I had to define this, as I did not see where it was defined in the samples repo
class args:
    def __init__(self, host, user, password, port, nocertval=True):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.disable_ssl_verification = nocertval



def connect(args):
    """
    Determine the most preferred API version supported by the specified server,
    then connect to the specified server using that API version, login and return
    the service instance object.
    """

    service_instance = None

    # form a connection...
    try:
        if args.disable_ssl_verification:
            service_instance = SmartConnect(host=args.host,
                                            user=args.user,
                                            pwd=args.password,
                                            port=args.port,
                                            disableSslCertValidation=True)
        else:
            service_instance = SmartConnect(host=args.host,
                                            user=args.user,
                                            pwd=args.password,
                                            port=args.port)

        # doing this means you don't need to remember to disconnect your script/objects
        atexit.register(Disconnect, service_instance)
    except IOError as io_error:
        print(io_error)

    if not service_instance:
        raise SystemExit("Unable to connect to host with supplied credentials.")

    return service_instance
