from getpass import getpass

from service_instance import connect, args
from pyVmomi import vim


user = open(".login").read().strip()
hostname = open(".hostname").read().strip()

vargs = args(hostname, user, getpass(f"Password for {user}: "), 443, True)

si = connect(vargs)

abt = si.content.about

print(abt)
