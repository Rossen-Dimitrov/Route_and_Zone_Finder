with open('settings.txt') as credentials:
    lines = [line.strip() for line in credentials.readlines()]

TACACS_PASS = lines[0].split(' = ')[1]
EVI_ROUTER = lines[1].split(' = ')[1]
JUMP_SERVER_IP = lines[2].split(' = ')[1]
JUMP_USER = lines[3].split(' = ')[1]
JUMP_PASS = lines[4].split(' = ')[1]
FW_IP = lines[5].split(' = ')[1]
