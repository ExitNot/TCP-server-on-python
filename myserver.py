#!/usr/bin/env python3
import socket 
import sys
import os
import re
import time
# import mv_dots

msglen = 100  # length of message to receive
buffer = ''  # Global buffer oriented for solving problem with merged msg


# This function read data ether from recv() method or from global buffer
# Эта функция может быть улучшена до универсальной
def read_data(c, flag):
    f_data = ''
    global buffer

    if buffer != '':
        while True:
            if buffer.find('\a\b') != -1:
                break
            f_data = c.recv(msglen).decode()
            buffer = buffer + str(f_data)
            f_data = ''
        for iterator, char in enumerate(str(buffer)):
            if char == '\a' and str(buffer[iterator + 1]) == '\b':
                break
            f_data += char

        buffer = buffer[len(f_data) + 2:]
    else:
        while True:
            f_data = str(f_data) + c.recv(msglen).decode()
            sys.stderr.write('client: %s\n' % str(f_data))
            if len(f_data) < 1:
                break

            if flag == 'username' or flag == 'ok' or flag == 'recharge' or flag == 'full_power':
                if len(f_data) > 12:
                    break
            if flag == 'confirm':
                if len(f_data) > 7:
                    break
            if flag == 'message':
                if len(f_data) > 100:
                    break

            if f_data.find('\a\b') != -1:
                break
    extra_str = ''
    for iterator, char in enumerate(str(f_data)):
        if char == '\a' and str(f_data[iterator + 1]) == '\b':
            break
        extra_str += char

    if buffer == '':
        buffer = f_data[len(extra_str) + 2:]
    f_data = extra_str
    print('what is going on in buffer    f_data :: buffer  =  ' + str(f_data) + ' :: ' + buffer)
    # limits are smaller in case of absence of '\a\b'
    if flag == 'username' or flag == 'ok' or flag == 'recharge' or flag == 'full_power':
        if len(f_data) > 10:
            return 'SERVER_SYNTAX_ERROR'
    if flag == 'confirm':
        if len(f_data) > 5:
            return 'SERVER_SYNTAX_ERROR'
    if flag == 'message':
        if len(f_data) > 98:
            return 'SERVER_SYNTAX_ERROR'

    return f_data


# process authentication and check validity of client key
def authentication(c):
    server_key = 54621
    client_key = 45328
    f_data = ''
    global buffer

    # Тут мнене нужна оптимизация
    f_data = read_data(c, 'username')
    if f_data == 'SERVER_SYNTAX_ERROR':
        f_back_msg = '301 SYNTAX ERROR\a\b'
        c.sendall(bytes(f_back_msg, 'ascii'))
        sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
        return False
    # creating the answer msg for client with hash of his name
    word_hash = 0
    for iterator, char in enumerate(str(f_data)):
        word_hash += ord(char)
    word_hash = (word_hash * 1000) % 65536
    f_back_msg = str((word_hash + server_key) % 65536) + '\a\b'
    c.sendall(bytes(f_back_msg, 'ascii'))
    sys.stderr.write('server: %s\n' % f_back_msg)

    # receiving CLIENT_CONFIRMATION
    f_data = read_data(c, 'confirm')
    if f_data == 'SERVER_SYNTAX_ERROR':
        f_back_msg = '301 SYNTAX ERROR\a\b'
        c.sendall(bytes(f_back_msg, 'ascii'))
        sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
        return False
    # if len(f_data) < 1:
    #     back_msg = '300 LOGIN FAILED\a\b'
    #     c.sendall(bytes(back_msg, 'ascii'))
    #     sys.stderr.write('server: SERVER_LOGIN_FAILED\n')
    #     return False

    client_key_check = int(f_data)
    client_key_check = (client_key_check - word_hash) % 65536
    if client_key_check != client_key:
        f_back_msg = '300 LOGIN FAILED\a\b'
        c.sendall(bytes(f_back_msg, 'ascii'))
        sys.stderr.write('server: SERVER_LOGIN_FAILED\n')
        return False
    else:
        f_back_msg = '200 OK\a\b'
        c.sendall(bytes(f_back_msg, 'ascii'))
        sys.stderr.write('server: SERVER_OK\n')
        return True


def move_command(c):
    c.sendall(bytes('102 MOVE\a\b', 'ascii'))
    sys.stderr.write('server: SERVER_MOVE\n')


def left_command(c):
    c.sendall(bytes('103 TURN LEFT\a\b', 'ascii'))
    sys.stderr.write('server: SERVER_TURN_LEFT\n')


def right_command(c):
    c.sendall(bytes('104 TURN RIGHT\a\b', 'ascii'))
    sys.stderr.write('server: SERVER_TURN_RIGHT\n')


# pick_up_command
def pick_up(c):
    c.sendall(bytes('105 GET MESSAGE\a\b', 'ascii'))
    sys.stderr.write('server: SERVER_PICK_UP\n')

    f_data = read_data(connection, 'message')
    if f_data == 'SERVER_SYNTAX_ERROR':
        back_msg = '301 SYNTAX ERROR\a\b'
        c.sendall(bytes(back_msg, 'ascii'))
        sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
        return False
    # f_data = c.recv(msglen).decode()
    # sys.stderr.write('client: %s\n' % str(f_data))
    if str(f_data) == '\a\b':  # means we don't find the message.
        # Пока хер знает
        return False
    else:
        c.sendall(bytes('106 LOGOUT\a\b', 'ascii'))
        return True


# Generate vector with correct movement direction. Return's needed command {'move', 'left', 'right'}
# This also process case when first point is == to second
def direction_calc(x1, x2, y1, y2):
    # actual_course
    act_cour = [x2 - x1, y2 - y1]  # [0, 1] is moving up by y axis, [0, -1] is moving down
    if x2 - x1 == 0 and y2 - y1 == 0:
        sys.stderr.write('Error: robot don\'t move forward\n')
        return 'move'
    if x2 > 2:  # [-1, 0]
        if act_cour[0] == -1:
            return 'move'
        if act_cour[0] == 1:
            if y2 > -2:
                return 'right'
            else:
                return 'left'
        if act_cour[1] == -1:
            return 'right'
        if act_cour[1] == 1:
            return 'left'
    if x2 < -2:  # [ 1, 0]
        if act_cour[0] == -1:
            if y2 > -2:
                return 'right'
            else:
                return 'left'
        if act_cour[0] == 1:
            return 'move'
        if act_cour[1] == -1:
            return 'left'
        if act_cour[1] == 1:
            return 'right'
    if y2 > 2:  # [ 0, -1]
        if act_cour[0] == -1:
            return 'left'
        if act_cour[0] == 1:
            return 'right'
        if act_cour[1] == -1:
            return 'move'
        if act_cour[1] == 1:
            if x2 > -2:
                return 'left'
            else:
                return 'right'
    if y2 < -2:  # [ 0, 1]
        if act_cour[0] == -1:
            return 'right'
        if act_cour[0] == 1:
            return 'left'
        if act_cour[1] == -1:
            if x2 > -2:
                return 'left'
            else:
                return 'right'
        if act_cour[1] == 1:
            return 'move'


# This func. process coordinates queue that contain only 2 elem last and cur position
def coord_queue(last, cur):
    queue = [last, cur]
    # print('last :: cur\n' + str(last) + ' :: ' + str(cur))
    return queue


if len(sys.argv) != 2:
    sys.stderr.write('Run program as \'myserver <port>\'\n')
# Create a TCP/IP socket
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
listener.bind(('localhost', int(sys.argv[1])))
sys.stderr.write('starting up on %s port %s\n' % ('localhost', sys.argv[1]))

# Listen for incoming connections
listener.listen(1024)
coordinates = []
while True:
    # Wait for a connection
    sys.stderr.write('\n+=============================================+\nWaiting for a connection\n')
    connection, client_addr = listener.accept()
    # if connection/listener.fileno() == -1:
    #     sys.stderr.write('connection from %s\n' % str(client_addr))
    #     continue

    child_pid = os.fork()  # fork returns process id of the child - stored in the parent
    if child_pid != 0:  # we are in the parent thread
        connection.close()
        continue
    listener.close()

    connection.settimeout(1)
    try:
        sys.stderr.write('connection from %s\n' % str(client_addr))

        # Receive the data and communicating
        while True:
            if not authentication(connection):
                break
            j = 0
            while True:
                if j < 2:
                    # 2 steps to the target area. Hire we can determine in witch direction we have to go.->
                    # square with corner coordinates [2,2], [2,-2], [-2,2] and [-2,-2]
                    move_command(connection)

                    data = read_data(connection, 'ok')
                    if data == 'SERVER_SYNTAX_ERROR':
                        back_msg = '301 SYNTAX ERROR\a\b'
                        connection.sendall(bytes(back_msg, 'ascii'))
                        sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
                        break
                    coordinates.append(re.findall(r'[+-]?\d+', str(data)))
                else:
                    # Here we determine direction to the target area
                    direction = direction_calc(int(str(coordinates[0][0])), int(str(coordinates[1][0])),
                                               int(str(coordinates[0][1])), int(str(coordinates[1][1])))
                    if direction == 'left':
                        left_command(connection)
                        data = read_data(connection, 'ok')
                        if data == 'SERVER_SYNTAX_ERROR':
                            back_msg = '301 SYNTAX ERROR\a\b'
                            connection.sendall(bytes(back_msg, 'ascii'))
                            sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
                            break
                    if direction == 'right':
                        right_command(connection)
                        data = read_data(connection, 'ok')
                        if data == 'SERVER_SYNTAX_ERROR':
                            back_msg = '301 SYNTAX ERROR\a\b'
                            connection.sendall(bytes(back_msg, 'ascii'))
                            sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
                            break
                    move_command(connection)

                    data = read_data(connection, 'ok')
                    if data == 'SERVER_SYNTAX_ERROR':
                        back_msg = '301 SYNTAX ERROR\a\b'
                        connection.sendall(bytes(back_msg, 'ascii'))
                        sys.stderr.write('server: SERVER_SYNTAX_ERROR\n')
                        break
                    # if len(data) < 1:
                    #     sys.stderr.write('Error: 0 msg %s\n' % len(data))
                    #     break
                    coordinates = coord_queue(coordinates[1], re.findall(r'[+-]?\d+', str(data)))
                # синтаксический распознаватель тут нужен 
                # Robot reaches the target area case
                if j == 0:
                    # print(str(coordinates))
                    if 2 >= int(str(coordinates[0][0])) >= -2 and 2 >= int(str(coordinates[0][1])) >= -2:
                        if pick_up(connection):
                            sys.stderr.write('SERVER_LOGOUT\n')
                            break
                else:
                    if 2 >= int(str(coordinates[1][0])) >= -2 and 2 >= int(str(coordinates[1][1])) >= -2:
                        if pick_up(connection):
                            sys.stderr.write('SERVER_LOGOUT\n')
                            break
                j = j + 1

            connection.close()
            break

    except socket.timeout as e:  # if timeout occurs
        print("Timeout!")
        connection.close()
