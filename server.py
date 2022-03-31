#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import logging
import websockets
import numpy as np
import time
import sqlite3
import os
import pandas as pd

logging.basicConfig()
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Server:
    def __init__(self):
        self.messageToBeSend = []  # to change to sql table

        self.conn = sqlite3.connect('server_database')  # connect to sql database
        self.c = self.conn.cursor()  # create a cursor

        self.c.execute('''CREATE TABLE IF NOT EXISTS log
                          ([mail] TEXT, [username] TEXT, [password] TEXT, [connected] TEXT, [websocket] TEXT)
                          ''')

        self.conn.commit()

        print(pd.DataFrame(self.c.execute('''SELECT username, mail, password FROM log''').fetchall(),
                           columns=['username', ' mail', 'password']))

    async def notify_users(self, message, user):
        await user.send(message)

    async def register(self, websocket):
        pass

    async def unregister(self, websocket):
        """unregister the user after he disconnects from the server:
        set connected to false"""

        self.c.execute(f'''UPDATE log
                        set connected = 'False'
                        WHERE websocket = (?)''', [str(websocket)])

        self.conn.commit()

    async def handle(self, websocket, _):

        await self.register(websocket)  # register the user if not already

        try:
            async for message in websocket:
                # data 0: type of request: msg, log, create account...

                data = message.split('|')

                if data[0] == 'login':

                    await self.login(data, websocket)

                elif data[0] == 'new_account':

                    await self.create_new_account(data, websocket)

                elif data[0] == 'msg':

                    await self.redirect_message(data, websocket)

        finally:
            await self.unregister(websocket)

    async def redirect_message(self, data, websocket):
        # if msg:
        # data 1: name of the conv
        # data 2: type
        # data 3: txt
        # data 4: pos of chunk
        # data 5: number of chuck
        # data 6: id of chunk

        # websocket = websocket from the guy who sent the message

        self.c.execute(f'''SELECT username FROM log
                       where websocket = (?) ''', [str(websocket)])

        username = list(self.c.fetchall()[0])[0]

        result = self.c.execute(f'''SELECT websocket, connected FROM log
                       where username = (?) ''', [data[1]]).fetchall()

        result = list(result[0])

        friend_websocket = result[0]
        is_friend_connected = result[1]

        msg = 'msg|' + username + ''.join(['|' + data[i] for i in range(2, 7)])

        if is_friend_connected == 'True':
            await self.notify_users(msg, friend_websocket)
        else:
            self.messageToBeSend.append([data[1], msg])

    async def create_new_account(self, data, websocket):
        a = self.new_account(data, websocket)
        # 'a' is either log if the creation of the account succeed or the type of error

        if a == 'log':
            print('new log')
            msg = 'Newlog|true'
        else:
            msg = 'Newlog|false|' + a

        await self.notify_users(msg, websocket)

    async def login(self, data, websocket):
        a = self.check_password(data)
        # 'a' is either False if the connection failed or the username of the user

        if a == 'false':  # if the user failed to connect
            await self.notify_users('log|false', websocket)

        else:
            # else notify him the success and communicate the username
            await self.notify_users('log|true|' + a, websocket)

            self.c.execute(f'''UPDATE log
                        set websocket = (?), connected = 'True'
                        WHERE username = (?)
                       ''', [str(websocket), a])

            self.conn.commit()

            # if the user as message for him:
            for msg in self.messageToBeSend:
                if msg[0] == a:
                    await self.notify_users(msg[1], websocket)
                    self.messageToBeSend.remove(msg)

    def check_password(self, request):
        is_ok = self.c.execute(
            f'''SELECT
                        CASE WHEN EXISTS 
                        (
                            SELECT username FROM log 
                            WHERE mail = (?) AND password = (?)
                        )
                        THEN 'true'

                        ELSE 'false'
                    END
                    ''', [request[1], request[2]]).fetchall()

        is_ok = list(is_ok[0])[0]

        if is_ok == 'true':
            self.c.execute('''SELECT username FROM log 
                              where mail = (?) AND password = (?)'''
                           , [request[1], request[2]])

            return list(self.c.fetchall()[0])[0]

        else:
            return 'false'

    def new_account(self, request, websocket):
        # request = ['new_account', mail, username, password]

        if not request[1]:
            return 'please enter a valid mail'
        elif not request[2]:
            return 'please enter a valid user name'

        self.c.execute(f''' SELECT
                                CASE WHEN EXISTS 
                                (
                                    SELECT username FROM log 
                                    WHERE mail = (?)
                                )
                                THEN 'TRUE'
                                ELSE 'FALSE'
                            END
                            ''', [request[1]])

        is_mail_taken = list(self.c.fetchall()[0])[0]

        self.c.execute(f''' SELECT
                            CASE WHEN EXISTS 
                            (
                                SELECT * FROM log WHERE username = (?)
                            )
                            THEN 'TRUE'
                            ELSE 'FALSE'
                        END
                            ''', (request[2],))

        is_username_taken = list(self.c.fetchall()[0])[0]

        if is_mail_taken == 'TRUE':
            return 'this mail is already taken'

        elif is_username_taken == 'TRUE':
            return 'this user name is already taken'

        elif len(str(request[3])) < 6:
            return 'your password is too short'

        else:

            request = request[1:] + ['True', str(websocket)]
            add_to_table = '''INSERT INTO log(mail, username, password, connected, websocket) VALUES (?, ?, ?, ?, ?)'''
            self.c.execute(add_to_table, request)

            self.conn.commit()

            return 'log'


server = Server()

start_server = websockets.serve(server.handle, "0.0.0.0", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
print("server on")
asyncio.get_event_loop().run_forever()


