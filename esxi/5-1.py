# SYS 350 w/ Ryan Gillen
# Milestone 5.1 Automation w/ PyVMomi
# Matt C

from getpass import getpass

from service_instance import connect, args
from pyVmomi import vim


def get_vms(service_instance, vm_name=None):
    """
    Searches for VMs by name, returning all VMs if no name is provided.
    """
    content = service_instance.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )

    vms = []
    for vm in container_view.view:
        if vm_name is None or vm_name.lower() in vm.name.lower():
            vms.append(vm)
    container_view.Destroy()
    return vms


user = open(".login").read().strip()
hostname = open(".hostname").read().strip()

vargs = args(hostname, user, getpass(f"Password for {user}: "), 443, True)

si = connect(vargs)

abt = si.content.about
session_manager = si.content.sessionManager
user_session = session_manager.currentSession

if not user_session:
    print("How'd we get here??")
    exit(1)

username = user_session.userName
print(f"Signed in as {username} from {user_session.ipAddress}")
print(f"Server info: {abt.fullName}")

query = input("Search for VMs named: ")

vms = get_vms(si, query)

for vm in vms:
    name = vm.name
    config = vm.config
    hw = config.hardware

    pstate = vm.runtime.powerState
    pwr = "On" if pstate == vim.VirtualMachinePowerState.poweredOn else "Off"

    ncpu = hw.numCPU
    mem = hw.memoryMB

    addr = "Unknown"
    if vm.guest.ipAddress:
        addr = vm.guest.ipAddress

    print(f"\n----------\nINFO : {name}\n----------")
    print(f"Guest is {pwr}")
    print(f"CPU Cores: {ncpu}")
    print(f"RAM MB: {mem}")
    if pwr == "On":
        print(f"IP Address: {addr}")

    # print(str(config))
