import time
from netmiko import redispatch
from settings import TACACS_PASS, FW_IP


class FireWallCon:
    def __init__(self, jump_connection):
        self.jump_connection = jump_connection
        self.log = ''

    def connect(self):
        try:
            self.jump_connection.write_channel(FW_IP + '\n')
            time.sleep(3)
            jump_server_output = self.jump_connection.read_channel()
            # print(jump_server_output)
            if 'The authenticity of host' in jump_server_output:
                self.jump_connection.write_channel('yes\n')

            if 'Password' in jump_server_output:
                self.jump_connection.write_channel(TACACS_PASS)
            redispatch(self.jump_connection, device_type='paloalto_panos')
            self.log += f"Connected to: {self.jump_connection.find_prompt().split('@')[1].split('> ')[0]}"
            return self.jump_connection

        except:
            self.log += (f"Connection !!! FAILED !!!\n"
                         f"Please check password in settings.py and the\n"
                         f"connectivity to FW {FW_IP}")
            exit()

    def send_commands(self, command, string=None, wait=2):
        """sending commands to current connection"""
        output = self.jump_connection.send_command(command, expect_string=string)
        time.sleep(wait)
        # if string not in output:
        #     output = pa_connection.send_command(command, expect_string=string)
        #     time.sleep(wait)
        return output

    def disconnect(self):
        if self.jump_connection:
            self.jump_connection.disconnect()
        self.log += "\nDisconnected from PA FireWall\n"
