class Network:
    def __init__(self, ip, host_mask, network, net_mask, fw_name=None, interface=None, zone=None):
        self.host = ip
        self.host_mask = host_mask
        self.network = network
        self.net_mask = net_mask
        self.fw_name = fw_name
        self.interface = interface
        self.zone = zone

    def __str__(self):
        return f"{self.host}/{self.host_mask} - {self.network}/{self.net_mask} - {self.fw_name} - {self.zone}"
