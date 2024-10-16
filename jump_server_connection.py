from netmiko import ConnectHandler
from settings import JUMP_SERVER_IP, JUMP_USER, JUMP_PASS

DEVICE = {
    'device_type': 'terminal_server',
    'ip': JUMP_SERVER_IP,
    'username': JUMP_USER,
    'password': JUMP_PASS,
    'port': 22
}


class JumpServer:
    def __init__(self):
        self.jump_connection = None
        self.log = ''

    def connect(self):
        """Disconnects from device if connected"""
        try:
            self.jump_connection = ConnectHandler(**DEVICE)
            self.log += f"Connected to Jump Server: {self.jump_connection.find_prompt().upper().split()[0][8:17]}\n"
        except:

            self.log += (f"Connection !!! FAILED !!!\n"
                         f"Please check password in settings.txt and the\n "
                         f"connectivity to JUMP SERVER {JUMP_SERVER_IP}\n")
            exit()
        # print(self.jump_connection.read_channel())
        return self.jump_connection

    def disconnect(self):
        """Disconnects from device if connected"""
        if self.jump_connection:
            self.jump_connection.disconnect()
            self.log += "\nDisconnected from Jump Server\n"
