import time
from netmiko import redispatch
from settings import TACACS_PASS, EVI_ROUTER


class RouterCon:
    def __init__(self, jump_connection):
        self.jump_connection = jump_connection
        self.log = ''

    def connect(self):
        self.jump_connection.write_channel(EVI_ROUTER + '\n')
        time.sleep(1)
        jump_server_output = self.jump_connection.read_channel()
        if 'The authenticity of host' in jump_server_output:
            self.jump_connection.write_channel('yes\n')
            time.sleep(1)
            jump_server_output += self.jump_connection.read_channel()

        try:
            if 'assword' in jump_server_output:
                self.jump_connection.write_channel(TACACS_PASS + '\n')
                time.sleep(1)
                redispatch(self.jump_connection, device_type='hp_comware')
                self.log += f"Connected to: {self.jump_connection.find_prompt()}\n"
            else:
                self.log += "No password prompt detected. Connection might have failed.\n"
                return None

        except Exception as e:
            self.log += (f"Connection !!! FAILED !!!\n"
                         f"Please check password in settings.txt and the\n"
                         f"connectivity to EVI Router {EVI_ROUTER}\nError: {str(e)}\n")
            exit()
        return self.jump_connection

    def send_commands(self, command):
        """sending commands to current connection"""
        output = self.jump_connection.send_command(command)

        return output

    def disconnect(self):
        """Disconnects from device if connected"""
        if self.jump_connection:
            self.jump_connection.disconnect()
        self.log += "\nDisconnected from EVI Router\n"
