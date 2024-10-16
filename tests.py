import ipaddress

# Define the IP and the network
ip = ipaddress.ip_address('10.2.20.193')
network = ipaddress.ip_network('10.2.20.192/26')

# Check if the IP is in the network
if ip in network:
    print(f"{ip} is in {network}")
else:
    print(f"{ip} is NOT in {network}")