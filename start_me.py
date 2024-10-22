from threading import Thread
from tkinter import Tk, Label, Button, Text
from firewall_connection import FireWallCon
from jump_server_connection import JumpServer
from network_objekt import Network
from router_connection import RouterCon
from static_routes_and_firewalls import DXC_HUB_FW, pa_fw_mapping, sap_fw_mapping
import ipaddress
import sys
import re

bcn_networks_list = []
bcn_directly_connected_list = []
sap_networks_list = []
pa_networks_list = []
vsx_firewall_list = []
check_point_hub = []
valid_ip_list = []
valid_net_list = []
logs = []


def start_program():
    global bcn_networks_list
    global bcn_directly_connected_list
    global sap_networks_list
    global pa_networks_list
    global vsx_firewall_list
    global valid_ip_list
    global valid_net_list
    global check_point_hub
    global logs

    bcn_networks_list = []
    bcn_directly_connected_list = []
    sap_networks_list = []
    pa_networks_list = []
    vsx_firewall_list = []
    valid_ip_list = []
    check_point_hub = []
    logs = []

    refresh_log('Starting...')
    Thread(target=run_start_program).start()


def refresh_log(text):
    logs_window.delete("1.0", 'end')
    if text == "!" and "!" in logs[-1]:
        text = logs.pop(-1)
        text += '!'
    logs.append(text)
    logs_window.insert('end', '\n'.join(logs))
    logs_window.update_idletasks()


def check_ip_in_subnets(ip_obj, subnet_dicts):
    # Loop through each dictionary of subnets
    for name, subnets in subnet_dicts.items():
        for subnet in subnets:
            try:
                net_obj = ipaddress.IPv4Network(subnet)
                if ip_obj in net_obj:
                    return True, name, net_obj
            except ValueError as e:
                refresh_log(str(e))
    return False, None, None


def run_start_program():
    logs_window.delete("1.0", 'end')
    result_window.delete("1.0", 'end')
    ip_entry = ip_list_entry.get('1.0', 'end').strip()
    ip_list = ip_entry.split('\n')

    # checking for correct entry

    all_ip_are_valid = True

    for ip in ip_list:
        ip = re.split('[-_/]', ip)[0]
        try:
            ip = ipaddress.IPv4Address(ip)
            valid_ip_list.append(ip)
        except ValueError as e:
            all_ip_are_valid = False
            refresh_log(str(e))
    if not all_ip_are_valid:
        sys.exit()

    # Check each valid IP against the subnets
    if valid_ip_list:
        hub_control_list = []
        for ip_obj in valid_ip_list:
            found_in_dxc, dxc_name, net_obj = check_ip_in_subnets(ip_obj, DXC_HUB_FW)
            if found_in_dxc:
                network_obj = Network(
                    str(ip_obj), host_mask=32,
                    network=net_obj.network_address,
                    net_mask=net_obj.netmask,
                    fw_name=dxc_name, zone='N/A')
                check_point_hub.append(network_obj)
                hub_control_list.append(ip_obj)
        if hub_control_list:
            for ip_obj in hub_control_list:
                if ip_obj in valid_ip_list:
                    valid_ip_list.remove(ip_obj)

    if not valid_ip_list and not valid_net_list:
        if check_point_hub:
            refresh_log('Task Finished')
            result_ip_object_list = (bcn_networks_list
                                     + bcn_directly_connected_list
                                     + sap_networks_list
                                     + pa_networks_list
                                     + vsx_firewall_list
                                     + check_point_hub)
            result_ip_list = [str(obj) for obj in result_ip_object_list]
            result_window.insert('end', '\n'.join(result_ip_list))
        sys.exit()

    refresh_log('Connecting to Jump Server')
    jump = JumpServer()
    jump.log = ''
    jump_connection = jump.connect()
    refresh_log(jump.log)
    refresh_log('Connecting to EVI Router')
    evi_router = RouterCon(jump_connection)
    evi_router.log = ''
    evi_router.connect()
    refresh_log(evi_router.log)
    refresh_log('Collecting info from EVI Router')
    for ip in valid_ip_list:
        """ Sending commands for each IP Route """
        refresh_log("!")
        host_mask = '32'
        print(str(ip))
        command = f'display ip routing-table vpn-instance bcn-core {str(ip)}'
        output = evi_router.send_commands(command).splitlines()
        subnet = output[-1].split()[0]
        try:
            network, net_mask = subnet.split('/')
            interface = output[-1].split()[5]
            directly_connected = output[-1].split()[1]
        except ValueError:
            subnet = output[-2].split()[0]
            network, net_mask = subnet.split('/')
            interface = output[-2].split()[5]
            directly_connected = output[-2].split()[1]

        if interface in pa_fw_mapping:
            network_obj = Network(ip, host_mask, network, net_mask, pa_fw_mapping[interface])
            pa_networks_list.append(network_obj)

        elif interface in sap_fw_mapping:
            zone = None
            if sap_fw_mapping[interface] == 'MSVX-NSX-T-DMZ':
                zone = 'DMZ-bisgw150_bisigw2-vlan2010'
            network_obj = Network(ip, host_mask, network, net_mask, fw_name=sap_fw_mapping[interface], zone=zone)
            sap_networks_list.append(network_obj)

        elif directly_connected == "Direct":
            network_obj = Network(ip, host_mask, network, net_mask, zone="BCN", interface='Directly Connected')
            vsx_firewall_list.append(network_obj)
        else:
            network_obj = Network(ip, host_mask, network, net_mask, zone='BCN')
            bcn_networks_list.append(network_obj)

    evi_router.disconnect()
    logs_window.update_idletasks()
    jump.disconnect()
    logs_window.update_idletasks()

    if pa_networks_list:
        refresh_log('Connecting to Jump Server')
        jump_connection = jump.connect()
        refresh_log(jump.log)
        refresh_log('Connecting to PA FireWall')
        firewall = FireWallCon(jump_connection)
        firewall.log = ''
        firewall.connect()
        refresh_log(firewall.log)
        refresh_log('Collecting info from PA FireWall')
        for subnet in pa_networks_list:
            """ Finding zones """
            refresh_log('!')
            command = f'test routing fib-lookup virtual-router {subnet.fw_name} ip {subnet.host}'

            output = firewall.send_commands(command, r"---------", wait=2)
            if 'via' in output:
                interface = output.strip().splitlines()[6].split()[3][:-1]
            elif 'to host' in output:
                interface = output.strip().splitlines()[6].split()[3]
            else:
                interface = output.strip().splitlines()[6].split()[1][:-1]

            command = f"show interface {interface} | match Zone:"
            output = firewall.send_commands(command, string=r"virtual system:", wait=0.2)
            zone = output.split()[1][:-1]
            subnet.interface = interface
            subnet.zone = zone

            command = f"show interface {interface} | match address:"
            output = firewall.send_commands(command, string=r"Interface IP address:", wait=0.2)
            result = output.split()[3]
            gw, mask = result.split('/')
            subnet.network = gw
            subnet.net_mask = mask

        firewall.disconnect()
        refresh_log(firewall.log)
        jump.disconnect()
        refresh_log(jump.log)

    refresh_log('Task Finished')
    result_ip_object_list = (bcn_networks_list
                             + bcn_directly_connected_list
                             + sap_networks_list
                             + pa_networks_list
                             + vsx_firewall_list
                             + check_point_hub)
    result_ip_list = [str(obj) for obj in result_ip_object_list]
    result_window.insert('end', '\n'.join(result_ip_list))


window = Tk()
window.title('PA Zone Finder')
# window.minsize(width=900, height=700)
window.config(padx=20, pady=20)

#     window.grid_columnconfigure(i, weight=1)
window.grid_columnconfigure(1, weight=2)
window.grid_rowconfigure(1, weight=1)  # Only the second row needs to expand

ip_label = Label(text="Enter IP addresses", width=20)
ip_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

logs_label = Label(text="L O G  W I N D O W", width=40)
logs_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

# Frame for ip_list Text widget
ip_list_entry = Text(window, height=40, width=20)
ip_list_entry.focus()
ip_list_entry.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Frame for logs Text widget
logs_window = Text(window, height=40)
logs_window.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

# Frame for result Text widget
result_window = Text(window, height=40, width=80)
result_window.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

start_btn = Button(text='S T A R T', command=start_program)
start_btn.config(padx=40)
start_btn.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

window.mainloop()
