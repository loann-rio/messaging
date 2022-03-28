#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import logging
import websockets
import numpy as np

logging.basicConfig()
try:
    log = np.load('log.npy')
except FileNotFoundError:
    np.save('log.npy', np.array([['mail', 'name', 'password']]))
    log = np.array([['mail', 'name', 'password']])

print(log)

USERS = []
username = []

messageToBeSend = []

# message = sender, receiver, message


async def notify_users(message, user):        
    await user.send(message)


async def register(websocket):
    if websocket not in USERS:
        USERS.append(websocket)
        username.append('None')
        
    print(f"new user connected: {len(USERS)} users connected ")
    # await notify_users("register" + str(websocket), websocket)


async def unregister(websocket):
    username.pop(USERS.index(websocket))

    USERS.remove(websocket)
    print("ur" + str(websocket))


async def handle(websocket, path):

    await register(websocket)
        
    try:
        async for message in websocket:
            # data 0: type of request: msg, log, create account...


            data = message.split('|')

            if data[0] == 'login':

                a = check_password(data, log)
                # 'a' is either False if the connection failed or the username of the user

                if a == 'false':  # if the user failed to connect
                    await notify_users('log|false', websocket)

                else:
                    # else notify him the success and communicate the username
                    await notify_users('log|true|'+a, websocket)
                    username[USERS.index(websocket)] = a

                    # if the user as message for him:
                    for msg in messageToBeSend:
                        if msg[0] == a:
                            await notify_users(msg[1], USERS[username.index(a)])
                            messageToBeSend.remove(msg)

            elif data[0] == 'new_account':

                a = new_account(data, log)
                # 'a' is either log if the creation of the account succeed or the type of error

                if a == 'log':
                    await notify_users('Newlog|true', websocket)
                else:
                    await notify_users('Newlog|false|'+a, websocket)    
           
            elif data[0] == 'msg':
                # if msg:
                # data 1: name of the conv
                # data 2: type
                # data 3: txt
                # data 4: pos of chunk
                # data 5: number of chuck
                # data 6: id of chunk

                msg = 'msg|'+username[USERS.index(websocket)]+'|'+data[2]+'|'+data[3]+'|'+data[4]+'|'+data[5]+'|'+data[6]

                if data[1] in username:
                    await notify_users(msg, USERS[username.index(data[1])])

                else:
                    messageToBeSend.append([data[1], msg])

    finally:
        await unregister(websocket)


def check_password(request, log):
    # request = [connection, mail, password]
    if request[1] in log:
        if str(log[np.where(log == request[1])[0][0]][2]) == str(request[2]):
            client_username = log[np.where(log == request[1])[0][0]][1]
            return client_username
    return 'false'


def new_account(request, log):
    # request = ['new_account', mail, username, password]
    if request[1] in log and request[1]:
        error = 'this mail is already taken'
    elif not request[1]:
        error = 'please enter a valid mail'
    elif request[2] in log and request[2]:
        error = 'this user name is already taken'
    elif not request[2]:
        error = 'please enter a valid user name'
    elif len(str(request[3])) < 6:
        error = 'your password is too short'
    else:
        request = request[1:]
        log = np.vstack([log, request])
        np.save('log.npy', log)
        return 'log'
    return error


start_server = websockets.serve(handle, "0.0.0.0", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
print("server on")
asyncio.get_event_loop().run_forever()


