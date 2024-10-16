

all_ip_are_valid = True
valid_ip_list_str = []

for ip in test_ip_list:
    looped_ip = re.split('[-_/]', ip)[0]
    try:
        ip_obj = ipaddress.ip_address(looped_ip)
        valid_ip_list_str.append(ip_obj)

    except ValueError as e:
        print(e)
        all_ip_are_valid = False


def check_ip_in_subnets(ip_obj, subnet_dicts):
    # Loop through each dictionary of subnets
    for name, subnets in subnet_dicts.items():
        for subnet in subnets:
            print(subnet)
            try:
                net_obj = ipaddress.ip_network(subnet)
            except ValueError as e:
                print(e)

            if ip_obj in net_obj:
                return True, name, subnet
    return False, None, None


# Check each valid IP against the subnets
for test_ip in valid_ip_list_str:
    found_in_dxc, dxc_name, dxc_subnet = check_ip_in_subnets(test_ip, DXC_HUB_FW)

    if found_in_dxc:
        print(f"{test_ip} found in DXC_HUB_FW under {dxc_name} in subnet {dxc_subnet}")
    else:
        print(f"{test_ip} not found in any subnet")