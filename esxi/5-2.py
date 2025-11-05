# SYS 350 w/ Ryan Gillen
# Milestone 5.2 More Automation
# Matt C

from getpass import getpass
import time

from service_instance import connect, args
from pyVmomi import vim
from pyVim.task import WaitForTask


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


def get_vm(si, vm_name):
    vms = get_vms(si, vm_name)
    vm = None
    if len(vms) == 0:
        print("NO VM FOUND")
    if len(vms) == 1:
        vm = vms[0]
    if not vm:
        print("No vm found: " + vm_name)
    return vm


def all_vm_status():
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


def set_vm_power(si, vm_name):

    vms = get_vms(si, vm_name)
    vm = None
    if len(vms) == 0:
        print("NO VM FOUND")
        return
    if len(vms) == 1:
        vm = vms[0]
    if not vm:
        print("No vm found: " + vm_name)
        return

    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
        print(f"Powering on virtual machine '{vm_name}'...")
        _ = vm.PowerOnVM_Task()
        print(f"Power on task initiated for '{vm_name}'.")
    elif vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        _ = vm.PowerOffVM_Task()
        print(f"Power off task initiated for '{vm_name}'.")


def snapshot(si, vm_name, snapshot_name, snapshot_description):
    vms = get_vms(si, vm_name)
    vm = None
    if len(vms) == 0:
        print("NO VM FOUND")
        return
    if len(vms) == 1:
        vm = vms[0]
    if not vm:
        print("No vm found: " + vm_name)
        return
    print(f"Creating snapshot '{snapshot_name}' for VM '{vm.name}'...")
    task = vm.CreateSnapshot_Task(
        name=snapshot_name,
        description=snapshot_description,
        memory=False,  # Include VM memory in snapshot
        quiesce=False,  # Quiesce guest file system
    )
    WaitForTask(task)
    if task.info.state == vim.TaskInfo.State.success:
        print(f"Snapshot '{snapshot_name}' created successfully.")
    else:
        print(f"Error creating snapshot: {task.info.error.localizedMessage}")


def get_snapshot_by_name(snapshot_list, name):
    """Recursively search for a snapshot by name."""
    for snapshot in snapshot_list:
        if snapshot.name == name:
            return snapshot.snapshot
        if snapshot.childSnapshotList:
            found_snapshot = get_snapshot_by_name(snapshot.childSnapshotList, name)
            if found_snapshot:
                return found_snapshot
    return None


def restore_snapshot(si, vm_name, snapshot_name):
    vms = get_vms(si, vm_name)
    vm = None
    if len(vms) == 0:
        print("NO VM FOUND")
        return
    if len(vms) == 1:
        vm = vms[0]
    if not vm:
        print("No vm found: " + vm_name)
        return

    snapshot_obj = get_snapshot_by_name(vm.snapshot.rootSnapshotList, snapshot_name)

    if not snapshot_obj:
        print(f"Error: Snapshot '{snapshot_name}' not found for VM '{vm_name}'.")
        return

    print(f"Reverting VM '{vm_name}' to snapshot '{snapshot_name}'...")
    task = snapshot_obj.RevertToSnapshot_Task()

    WaitForTask(task)

    if task.info.state == vim.TaskInfo.State.success:
        print(f"Successfully reverted VM '{vm_name}' to snapshot '{snapshot_name}'.")
    else:
        print(
            f"Failed to revert VM '{vm_name}' to snapshot '{snapshot_name}': {task.info.error.msg}"
        )


def reconfig_vm(si, vm_name, new_ram):
    vm = get_vm(si, vm_name)

    if not vm:
        print("Could not find " + vm_name)
        return

    vm_spec = vim.vm.ConfigSpec()
    vm_spec.memoryMB = int(new_ram)

    # Reconfigure the VM
    print(f"Reconfiguring VM '{vm_name}' to {new_ram} MB RAM...")
    task = vm.ReconfigVM_Task(vm_spec)
    WaitForTask(task)
    print(f"VM '{vm_name}' reconfigured successfully.")


def clone_vm(si, vm_name, new_name, snap_name):
    vm = get_vm(si, vm_name)

    if not vm:
        print("No vm found: " + vm_name)
        return

    parent_vm = vm

    snapshot_obj = get_snapshot_by_name(vm.snapshot.rootSnapshotList, snap_name)
    if not snapshot_obj:
        print("No snapshot found by " + snap_name)
        return

    resource_pool = parent_vm.resourcePool
    relospec = vim.vm.RelocateSpec()
    relospec.diskMoveType = "moveChildMostDiskBacking"
    relospec.pool = resource_pool

    # Configure the clone spec
    clonespec = vim.vm.CloneSpec(
        location=relospec,
        snapshot=snapshot_obj,
        powerOn=False,
    )

    # Get the folder to place the new VM in
    vm_folder = parent_vm.parent

    print(f"Creating linked clone '{new_name}'...")
    task = parent_vm.CloneVM_Task(folder=vm_folder, name=new_name, spec=clonespec)

    WaitForTask(task)

    if task.info.state == vim.TaskInfo.State.success:
        print(f"Successfully created linked clone '{new_name}'.")
    else:
        print(
            f"Failed to create linked clone. Error: {task.info.error.localizedMessage}"
        )


def destroy_vm(si, vm_name):
    vm = get_vm(si, vm_name)

    if not vm:
        print("No vm found: " + vm_name)
        return

    if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
        set_vm_power(si, vm_name)

    print(f"Destroying VM: {vm.name}")
    destroy_task = vm.Destroy_Task()
    WaitForTask(destroy_task)
    print(f"VM {vm.name} destroyed successfully.")


## END FUNCS

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

running = True

while running:
    c = input(
        "\n1) Query VM info\n2) Toggle VM power\n3) Snapshot VM\n4) Restore VM Snapshot\n5) Set VM RAM\n6) Make Linked Clone of VM\n7) Destroy VM\nq) Quit\n\nSelect: "
    )
    if c == "1":
        all_vm_status()
    elif c == "2":
        set_vm_power(si, input("VM Name: "))
    elif c == "3":
        vmn = input("VM Name: ")
        sn = input("Snapshot name: ")
        sd = input("Snapshot description: ")
        snapshot(si, vmn, sn, sd)
    elif c == "4":
        vmn = input("VM Name: ")
        sn = input("Restore snapshot: ")
        restore_snapshot(si, vmn, sn)
    elif c == "5":
        vmn = input("VM Name: ")
        nr = input("New RAM (in MB): ")
        reconfig_vm(si, vmn, nr)
    elif c == "6":
        vmn = input("Source VM Name: ")
        sn = input("Target snapshot: ")
        cn = input("Clone VM (dest) name: ")
        clone_vm(si, vmn, cn, sn)
    elif c == "7":
        vmn = input("DESTROY this vm: ")
        if input("(c)onfirm DESTROY VM " + vmn + ": ") == "c":
            destroy_vm(si, vmn)
        else:
            print("No action taken.")
    elif c == "q":
        running = False
    else:
        print("Unknown: " + c)
