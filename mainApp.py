import random
from interactives import (InputBox, Button)
from queue import Queue, Empty
import websocket
import _thread
import numpy as np
import pygame
import sqlite3
import os
import pandas as pd
import pickle  # use to encode and decode the image
import codecs
import cv2  # used to import an image

ip = ''

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# to do:
# divide big message into smaller chunk

# call function

# better UI:
#    nicer message box
#    background

# something to add friend
# image to send selection
# make it work over multiple network
# parameter conv

# sql files:
# array of conv with participants
# array of conv with messages.
# messages = txt, from, to, time, type

# in server: same +
# logs
# for each person:
# pseudo, mail, password, description, friends, image, last connection + useless information

q = Queue()

pygame.init()

im = cv2.imread('test_image.jpg')
obj_base64string = codecs.encode(pickle.dumps(im, protocol=pickle.HIGHEST_PROTOCOL), "base64").decode('latin1')


def ws_message(_, new_message):
    q.put(new_message)


def ws_thread():
    ws.run_forever()


ws = websocket.WebSocketApp(f"ws://{ip}:6789/", on_message=ws_message)

# Start a new thread for the WebSocket interface
_thread.start_new_thread(ws_thread, ())


def resize_text(data) -> list:
    """function used to resize the text of a message in the way that it fit,
     it returns a list of line from a single line"""

    text = [' ']
    for word in data.split():
        text[-1] += ' ' + word  # first add a word to the last line

        txt_surface = pygame.font.Font(None, 23).render(text[-1], True, (0, 0, 0))  # init the text surface
        if txt_surface.get_width() > 420:  # check the width of this surface
            # if the line is too long remove the new word and create a new line
            ind = len(text[-1]) - text[-1][::-1].index(' ')
            text.append(word)
            text[-2] = text[-2][:ind]

    return text


class Main:
    def __init__(self):
        self.screen = pygame.display.set_mode((1200, 800))
        self.username = ''  # will fill after the connection of the user
        self.conv = ''  # conv is the name of what is showed in the main page
        self.current_conv = None  # current conv is the pandas array with the conv we are working on
        self.list_conv = []
        self.conn = None
        self.c = None
        self.long_message = dict()  # dict of long message I didn't completely receive
        self.new_incoming_call = None  # is either None or the name of the user calling

    def init_main(self) -> None:
        """this function is used to get all the conversation that are saved in a file
        and if the file do not exist yet, it will create it; for now it's created with one contact
        to have something to show on the main page. """
        self.conn = sqlite3.connect('message_database'+self.username)
        self.c = self.conn.cursor()

        self.c.execute('''
                  CREATE TABLE IF NOT EXISTS conv
                  ([conv_id] INTEGER PRIMARY KEY, [conv_name] TEXT)
                  ''')

        self.conn.commit()

        self.c.execute(''' SELECT conv_name FROM conv''')

        self.list_conv = [i[0] for i in self.c.fetchall()]

        # If the user is not in any conv yet create one (should be change)
        if len(self.list_conv) == 0:
            self.create_new_conv()

        self.switch_current_conv(self.list_conv[0])

        self.main_window()

    def draw_login(self, wrong, input_boxes):

        self.screen.fill((250, 250, 250))
        self.screen.blit(pygame.font.Font(None, 300).render("Login", True, (220, 220, 220)), (150, 120))

        if wrong:
            self.screen.blit(pygame.font.Font(None, 25)
                             .render('wrong mail/password', True, (200, 30, 30)), (455, 510))

        for box in input_boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def login(self):

        input_box1 = InputBox(450, 360, 300, 60, False, "mail", size_text=28, size_hint=35, offset=(20, 20))
        input_box2 = InputBox(450, 440, 300, 60, True, 'password', offset=(20, 20))
        button = Button(630, 520, 120, 40, "continue", (130, 130, 130), (190, 150, 150), 36, 'centered')
        button2 = Button(960, 720, 190, 30, "create an account", (130, 130, 130), (210, 210, 210), 28, 'centered')

        input_boxes = [input_box1, input_box2, button, button2]

        wrong = False
        enter_key = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)

                for box in input_boxes:
                    enter_key = box.handle_event(event)
                    if enter_key:
                        break

            mail = input_box1.get_text()
            password = input_box2.get_text()

            self.draw_login(wrong, input_boxes)

            if button.active or enter_key:
                ws.send('login|'+mail+'|'+password)

            try:  # an error will occur when the queue will be empty, breaking the loop at the same time
                while True:
                    data = q.get(False).split('|')

                    if data[0] == 'log':
                        if data[1] == 'true':
                            self.username = data[2]
                            self.init_main()
                        else:
                            wrong = True
                            button.rect.y = 540
            except Empty:
                pass

            if button2.active:
                self.new_account()
                break

    def draw_new_account(self, error, input_boxes):
        self.screen.fill((250, 250, 250))
        self.screen.blit(pygame.font.Font(None, 200).render("new account", True, (220, 220, 220)), (170, 120))

        self.screen.blit(pygame.font.Font(None, 20).render(error, True, (200, 30, 30)), (455, 610))

        for box in input_boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def new_account(self):

        input_box1 = InputBox(450, 380, 300, 60, False, "mail", size_text=28, size_hint=35, offset=(20, 20))
        input_box2 = InputBox(450, 300, 300, 60, hint="user name")
        input_box3 = InputBox(450, 460, 300, 60, True, 'password', offset=(20, 20))
        input_box4 = InputBox(450, 540, 300, 60, password=True, hint='confirm password')

        button = Button(630, 620, 120, 40, "continue", (210, 130, 130), (250, 90, 90), 36, 'centered')
        button2 = Button(890, 720, 260, 30, "I already have an account", (130, 130, 130), (210, 210, 210), 28,
                         'centered')

        input_boxes = [input_box1, input_box2, input_box3, input_box4, button, button2]

        error = ''
        enter_key = None

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)
                for box in input_boxes:
                    enter_key = box.handle_event(event)
                    if enter_key:
                        break

            mail = input_box1.get_text()
            user_name = input_box2.get_text()
            password = input_box3.get_text()
            password2 = input_box4.get_text()

            self.draw_new_account(error, input_boxes)

            if button.active or enter_key:
                if password == password2:
                    row = f'new_account|{mail}|{user_name}|{password}'
                    ws.send(row)

                else:
                    error = 'please enter a valid password'

            try:
                while True:
                    data = q.get(False).split('|')

                    if data[0] == 'Newlog':
                        if data[1] == 'true':
                            self.username = user_name
                            self.init_main()

                        else:
                            error = data[2]
            except Empty:
                pass

            if error:
                button.rect.y = 640

            if button2.active:
                self.login()

    def save_message(self, name_conv, type_message, txt, from_who) -> None:
        """ this function save every message sent and received into the sql file and into the pandas dataframe"""

        # data[1] is the name of the conv

        # if the table does not exist create it:
        self.c.execute(f'''
                  CREATE TABLE IF NOT EXISTS {name_conv}
                  ([conv] TEXT, [type] TEXT, [txt] TEXT, [from_who] TEXT)
                  ''')

        # insert the message in the conv table
        # the table use the form:
        # from, type, txt (, time)

        add_msg = f''' INSERT INTO {name_conv} (conv, type, txt, from_who) VALUES (?, ?, ?, ?) '''

        self.c.execute(add_msg, (name_conv, type_message, txt, from_who))

        self.conn.commit()

        # then in the pandas dataframe:

        # resize the text for it to fit in the window (from line to square)
        txt = pickle.loads(codecs.decode(txt.encode('latin1'), "base64")) if type_message == 'image' else txt

        txt = resize_text(txt) if type_message == 'txt' else txt

        self.current_conv.loc[len(self.current_conv.index)] = [name_conv, type_message, txt, from_who]

    def send_message(self, text, type_of_msg):
        """this function split the message in smaller message if the first one is too big then
        send it to the server. the ID and the pos of the message are used to merge the message at the reception. """
        size_chuck = 100000
        new_msg = []   # part of the global message
        id_message = random.randint(0, 100000000)  # choose a number probably not already in use

        self.save_message(self.conv, type_of_msg, text, self.username)

        while len(text) > size_chuck:  # split the message in chuck of size 100000
            new_msg.append(text[:size_chuck])
            text = text[size_chuck:]

        new_msg.append(text)

        # type_of_msg should be files / txt or image
        for i in range(len(new_msg)):
            ws.send(f'msg|{self.conv}|{type_of_msg}|{new_msg[i]}|{i}|{len(new_msg)}|{id_message}')

    def draw_main_window(self, boxes, height, box_select_conv):
        margin_x = 20

        self.screen.fill((230, 230, 230))

        pygame.draw.rect(self.screen, (250, 249, 223), [400, 75, 800, 700])  # main background rect
        pygame.draw.rect(self.screen, (250, 250, 250), [0, 75, 400, 725])   # friend selection background rect

        for box in box_select_conv:
            box.draw(self.screen)

        if self.current_conv is None:
            list_message = []
        else:
            list_message = [i for i in self.current_conv.iterrows()]

        for message in reversed(list_message):

            message = message[1]

            # message = [from, type, text]
            if message[1] == 'txt':
                nb_row = len(message[2])  # get the number of row for a single message

                height_message = 20 * nb_row + 20  # height of the message box, +20 is the margin

                if nb_row == 1:
                    width = pygame.font.Font(None, 23).render(message[2][0], True, (0, 0, 0)).get_width() + margin_x
                    # if there is only one row we can directly calculate its width
                else:
                    width = 440
                    # else we limit it at 440, should be upgraded to adapt to all kind of message

                if message[3] == self.username:
                    # if I sent the message place it at the right in blue
                    pos_x = 1150 - width
                    color = (0, 0, 175)
                else:
                    # else at the left and grey
                    pos_x = 450
                    color = (150, 150, 150)

                height -= height_message + 10  # change the reference height for the new msg

                if height > 735:
                    continue
                elif height+height_message < 75:
                    break

                pygame.draw.rect(self.screen, color, [pos_x, height, width, height_message], border_radius=15)
                # draw the message box

                for row in message[2]:
                    self.screen.blit(pygame.font.Font(None, 23).render(row, True, (250, 250, 250)),
                                     (pos_x + margin_x/2, height + 10 + 20 * message[2].index(row)))

            elif message[1] == 'image':

                surf = pygame.surfarray.make_surface(np.fliplr(np.rot90(message[2], 3)))

                width_image = surf.get_width()
                height_image = surf.get_height()

                new_height_image = (390/width_image)*height_image
                surf = pygame.transform.scale(surf, (390, new_height_image))

                height -= new_height_image+20

                if message[3] == self.username:
                    # if I sent the message place it at the right in blue
                    pos_x = 750
                    color = (0, 0, 175)
                else:
                    # else at the left and grey
                    pos_x = 450
                    color = (150, 150, 150)

                pygame.draw.rect(self.screen, color, [pos_x, height, 400, (390/width_image)*height_image+10])
                self.screen.blit(surf, (pos_x + 5, height + 5))

        pygame.draw.rect(self.screen, (230, 230, 230), [0, 0, 1200, 75])

        pygame.draw.rect(self.screen, (230, 230, 230), [400, 735, 800, 65])

        pygame.draw.line(self.screen, (100, 100, 100), (400, 0), (400, 800), 1)
        pygame.draw.line(self.screen, (100, 100, 100), (0, 75), (1200, 75), 1)

        self.screen.blit(pygame.font.Font(None, 30).render(str(self.conv), True, (0, 0, 0)), (450, 20))

        for box in boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def handle_message(self):
        """ this function is use the handle the incoming messages:
        if the message is in more than on part it will keep track of the non-complete msg and merge the part
        at the end"""

        try:
            while True:
                data = q.get(False).split('|')
                # data 0: type of request: msg, log, create account, ...

                if data[0] == 'msg':
                    # if msg:
                    # data 1: name of the conv
                    # data 2: type
                    # data 3: txt
                    # data 4: pos of chunk
                    # data 5: number of chuck
                    # data 6: id of chunk
                    if int(data[5]) == 1:  # if the message is already complete: save it directly
                        self.save_message(data[1], data[2], data[3], data[1])

                    else:
                        msg = self.long_msg(data)
                        if msg:
                            self.save_message(data[1], data[2], msg, data[1])

                elif data[0] == 'incoming_call':
                    # if incoming call
                    # data 1: name conv
                    # data 2: start/stop
                    if data[2] == 'start':
                        self.new_incoming_call = data[1]
                    else:
                        self.new_incoming_call = None

        except Empty:
            pass

    def scroll_message(self, event, offset):

        height_top_message = 0
        list_message = []
        if self.current_conv is not None:
            list_message = [i for i in self.current_conv.iterrows()]

        for message in list_message:
            height_top_message += 20 * len(message[1][2]) + 20 if message[1][1] == 'txt' else 400

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 5 and offset >= 710:
                offset -= 35
            elif event.button == 4 and offset - height_top_message < 400:
                offset += 35
        return offset

    def long_msg(self, data):
        if data[6] in self.long_message:

            self.long_message[data[6]][0] += 1  # keep track of the number of chunk received
            self.long_message[data[6]][1][int(data[4])] = data[3]

            if self.long_message[data[6]][0] == int(data[5]):
                del self.long_message[data[6]]  # when the msg is complete: del the message from dict

                return "".join(self.long_message[data[6]][1])

        else:
            # create the key in the dict (the id)
            self.long_message[data[6]] = [1, [0 for _ in range(int(data[5]))]]
            self.long_message[data[6]][1][int(data[4])] = data[3]

    def create_new_conv(self):
        """ for now the user will only be able to create 2 person conv (because it's easier)"""
        friend_box = InputBox(20, 120, 360, 60, round_box=6, color=(44, 221, 41), color_text=(50, 50, 50))
        friend_button = Button(20, 200, 100, 50, 'choose', (0, 170, 0), (0, 200, 0), 25, offset='centered')
        boxes = [friend_box, friend_button]

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)
                for box in boxes:
                    box.handle_event(event)

            self.draw_new_conv(boxes)

            if friend_button.active and friend_box.text:
                # create a sql table for the conv
                # for now the conv have the name of the friend because only one friend

                self.c.execute(f'''
                          CREATE TABLE IF NOT EXISTS {friend_box.text}
                          ([conv] TEXT, [type] TEXT, [txt] TEXT, [from_who] TEXT)
                          ''')

                self.c.execute("SELECT max(conv_id) from conv")
                n = self.c.fetchone()[0]
                if n is None:
                    n = 1
                else:
                    n += 1

                add_to_table = '''INSERT INTO conv(conv_id, conv_name) VALUES (?, ?)'''
                self.c.execute(add_to_table, (n, friend_box.text))
                self.conn.commit()
                self.list_conv.append(friend_box.text)
                self.switch_current_conv(friend_box.text)
                return

    def draw_new_conv(self, boxes):
        self.screen.fill((250, 250, 250))
        self.screen.blit(pygame.font.Font(None, 72).render("create a new conv", True, (120, 120, 120)), (100, 100))

        for box in boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def switch_current_conv(self, new_conv):

        self.conv = new_conv

        self.c.execute(f''' SELECT * FROM {self.conv}''')

        self.current_conv = pd.DataFrame(self.c.fetchall(), columns=['conv', 'type', 'txt', 'from_who'])

        for row in self.current_conv.iterrows():
            if row[1][1] == 'txt':
                row[1][2] = resize_text(row[1][2])
            elif row[1][1] == 'image':
                # change the image in base 64 to a np.array
                row[1][2] = pickle.loads(codecs.decode(row[1][2].encode('latin1'), "base64"))

    def main_window(self):
        message_box = InputBox(500, 745, 600, 45, round_box=12, color=(44, 221, 41),
                               color_text=(50, 50, 50), offset=(15, 12), size_text=28)
        send_button = Button(1130, 750, 50, 35, 'send', (0, 170, 0), (0, 200, 0), 25, offset='centered')

        img_button = Button(430, 745, 50, 45, 'img')

        plus_button = pygame.Surface((40, 40))
        plus_button.fill((230, 230, 230))
        pygame.draw.line(plus_button, (100, 100, 100), (19, 4), (19, 36), 6)
        pygame.draw.line(plus_button, (100, 100, 100), (3, 19), (37, 19), 6)
        new_conv_button = Button(20, 20, 30, 30, image=plus_button)

        call_button = Button(1100, 20, 30, 30, 'call', offset='centered')

        boxes = [message_box, send_button, img_button, new_conv_button, call_button]

        box_select_friend = []
        h = 75
        for box in self.list_conv:
            box_select_friend.append(Button(0, h, 401, 76, box, offset='centered', color=(170, 170, 170),
                                            color2=(120, 120, 120), stroke=1))
            h += 75

        height = 710  # height is a datum for the position of the messages, the last message is draw at this height
        enter_key = None

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)

                for box in boxes:
                    enter_key = box.handle_event(event)
                    if enter_key:
                        break

                for box in box_select_friend:
                    box.handle_event(event)
                    if box.active:
                        self.switch_current_conv(box.text)
                        break

                height = self.scroll_message(event, height)

            self.handle_message()

            if call_button.active:
                call_button.active = False
                self.call()

            if img_button.active:
                img_button.active = False
                self.send_message(obj_base64string, 'image')

            if (send_button.active or enter_key) and message_box.text:
                self.send_message(message_box.text, 'txt')
                send_button.active = False  # reset button
                message_box.text = ''  # reset box text

            if new_conv_button.active:
                new_conv_button.active = False
                self.create_new_conv()

                if len(self.list_conv) != len(box_select_friend):
                    box_select_friend = []
                    h = 75
                    for box in self.list_conv:
                        box_select_friend.append(Button(0, h, 401, 76, box, offset='centered', color=(170, 170, 170),
                                                        color2=(120, 120, 120), stroke=1))
                        h += 75

            self.draw_main_window(boxes, height, box_select_friend)


class Call:
    def __init__(self, screen):
        self.screen = screen
        self.mute = False
        self.camera = False
        self.friend = ''
        self.close_call_button = Button(400, 600, )
        self.mute_button = Button()
        self.camera_button = Button()

        self.cam_off = pygame.image.load("image/cam_off.png")
        self.cam_on = pygame.image.load("image/cam_on.png")
        self.hang_out_phone = pygame.image.load("image/hang_out_phone.png")
        self.pick_up_phone = pygame.image.load("image/pick_up_phone.png")
        self.mic_off = pygame.image.load("image/mic_off.png")
        self.mic_on = pygame.image.load("image/mic_on.png")

    def start_call(self):
        ws.send(f'new_call|'+self.conv)

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

            try:
                while True:
                    data = q.get(False).split('|')
                    if data[0] == accept_call:
                        if data[1] == 'accepted':
                            self.call()
                        else:
                            # here make noise
                            return
            except Empty:
                pass

            self.screen.fill((100, 100, 100))


    def call(self):
        """this function is used to call/video-call someone it will get input from the webcam and send via
        websocket the compressed resultant file.
        At the same time, it will get the msg from the other user and draw it on the screen"""

        # first send a call request:
        #   first to the server to know if the other is connected
        #   if he is: send to the user a call request
        #   wait for the answer maybe: (should not interrupt anything else)

        # then if accepted: start call on both side
        # turn on/off mic, webcam
        # stop the call
        # maybe share screen

        vid = cv2.VideoCapture(0)

        friend_frame = None
        friend_sound = None

        done = False
        while not done:
            try:

                while True:
                    data = q.get(False).split('|')
                    if data[0] == 'video':

                        if int(data[5]) == 1:

                            friend_frame = data[3]
                        else:
                            msg = self.long_msg(data)
                            if msg:
                                friend_frame = msg

                    if data[0] == 'sound':
                        pass

            except Empty:
                pass

            # get sound and send it
            #
            #

            # get video and send it
            ret, frame = vid.read()

            self.draw_call_and_sound(friend_frame, friend_sound, frame)

            encoded_frame = codecs.encode(pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL),
                                          "base64").decode('latin1')

            size_chuck = 100000
            new_msg = []  # part of the global message
            id_message = random.randint(0, 100000000)  # choose a number probably not already in use

            while len(encoded_frame) > size_chuck:  # split the message in chuck of size 100000
                new_msg.append(encoded_frame[:size_chuck])
                encoded_frame = encoded_frame[size_chuck:]

            new_msg.append(encoded_frame)

            # type_of_msg should be files / txt or image
            for i in range(len(new_msg)):
                ws.send(f'video|{self.conv}|{type_of_msg}|{new_msg[i]}|{i}|{len(new_msg)}|{id_message}')

    def draw_call_and_sound(self, frame, sound, my_frame):
        """draw in large the image from the other guy and in small in the corner the image of the user"""
        if frame:
            frame = pickle.loads(codecs.decode(frame.encode('latin1'), "base64"))
            surf = pygame.surfarray.make_surface(np.fliplr(np.rot90(frame, 3)))
            surf = pygame.transform.scale(surf, (1200, 800))
            self.screen.blit(surf, (0, 0))
            pygame.display.flip()

    def incoming_call(self):
        pass


main = Main()
main.login()
