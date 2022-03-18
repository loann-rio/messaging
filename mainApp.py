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

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# to do:
# divide big message in smaller chunk
# call function
# better UI:
#    nicer message box
#    background
#    select friend
# something to add friend
# image to send selection
# implement SQL
# manage ram use
# make it work over multiple network

# sql files:
# list of friend
# array of conv with participants
# array of conv with messages.
# messages = txt, from, to, time, type

# in server: same +
# logs
# for each person:
# pseudo, mail, password, description, friends, image, last connection + useless information

q = Queue()

pygame.init()

im = cv2.imread('test2.jpg')

obj_base64string = codecs.encode(pickle.dumps(im, protocol=pickle.HIGHEST_PROTOCOL), "base64").decode('latin1')


def ws_message(_, new_message):
    q.put(new_message)


def ws_thread(_):
    ws.run_forever()


ws = websocket.WebSocketApp("ws://:6789/", on_message=ws_message)

# Start a new thread for the WebSocket interface
_thread.start_new_thread(ws_thread, ())


class Message:  # no use for now, might delete later
    def __init__(self, sender, text, time):
        self.sender = sender  # me or friend
        self.text = text
        self.time = time


def resize_text(data):
    # function used to resize the text of a message in the way that it fit
    text = [' ']
    for word in data.split():
        text[-1] += ' ' + word

        txt_surface = pygame.font.Font(None, 23).render(text[-1], True, (0, 0, 0))
        if txt_surface.get_width() > 420:
            ind = len(text[-1]) - text[-1][::-1].index(' ')
            text.append(word)
            text[-2] = text[-2][:ind]
    return text


class Main:
    def __init__(self):
        self.screen = pygame.display.set_mode((1200, 800))
        self.username = ''  # will fill after the connection of the user
        self.friend = ''  # friend is the on that's shows in the main page
        self.conv = {'user2': []}  # dict containing all conversation with all the contacts

    def init_main(self):
        """this function is used to get all the conversation that are saved in a file
        and if the file do not exist yet, it will create it; for now it's created with one contact
        to have something to show on the main page. """

        try:
            with open('saves'+self.username+'.pickle', 'rb') as handle:
                self.conv = pickle.load(handle)
        except FileNotFoundError:
            with open('saves' + self.username + '.pickle', 'wb') as handle:
                pickle.dump({'user2': []}, handle, protocol=pickle.HIGHEST_PROTOCOL)

        self.friend = list(self.conv.keys())[0]

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
        # self.screen.blit(pygame.font.Font(None, 190).render(", True, (220, 220, 220)), (170, 250))
        # self.screen.blit(pygame.font.Font(None, 190).render("", True, (220, 220, 220)), (170, 250))

        self.screen.blit(pygame.font.Font(None, 20).render(error, True, (200, 30, 30)), (455, 610))

        for box in input_boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def new_account(self):
        a = 20
        input_box1 = InputBox(450, 360+a, 300, 60, False, "mail", size_text=28, size_hint=35, offset=(20, 20))
        input_box2 = InputBox(450, 280+a, 300, 60, hint="user name")
        input_box3 = InputBox(450, 440+a, 300, 60, True, 'password', offset=(20, 20))
        input_box4 = InputBox(450, 520+a, 300, 60, password=True, hint='confirm password')

        button = Button(630, 600+a, 120, 40, "continue", (210, 130, 130), (250, 90, 90), 36, 'centered')
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

    def send_message(self, text, type_of_msg):
        # type_of_msg should be files / txt or image
        ws.send(f'msg|{self.friend}|{type_of_msg}|' + text)
        self.conv[str(self.friend)].append(['me', type_of_msg, resize_text(text) if type_of_msg == 'txt' else text])
        self.save()

    def draw_main_window(self, boxes, height):
        margin_x = 20

        self.screen.fill((230, 230, 230))

        pygame.draw.rect(self.screen, (250, 249, 223), [400, 75, 800, 700])  # main background rect
        pygame.draw.rect(self.screen, (250, 250, 250), [0, 75, 400, 725])   # friend selection background rect

        for message in reversed(self.conv[str(self.friend)]):
            if message[1] == 'txt':
                nb_row = len(message[2])  # get the number of row for a single message

                height_message = 20 * nb_row + 20  # height of the message box, +20 is the margin

                if nb_row == 1:
                    width = pygame.font.Font(None, 23).render(message[2][0], True, (0, 0, 0)).get_width() + margin_x
                    # if there is only one row we can directly calculate its width
                else:
                    width = 440
                    # else we limit it at 440, should be upgraded to adapt to all kind of message

                if message[0] == 'me':
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

                if height > 735+400:
                    height -= message[3]
                    continue
                elif height+600 < 75:
                    break

                obj_reconstituted = pickle.loads(codecs.decode(message[2].encode('latin1'), "base64"))
                # obj_reconstituted = np.fromstring(message[2])
                surf = pygame.surfarray.make_surface(np.fliplr(np.rot90(obj_reconstituted, 3)))

                width_image = surf.get_width()
                height_image = surf.get_height()

                new_height_image = (390/width_image)*height_image
                surf = pygame.transform.scale(surf, (390, new_height_image))

                height -= new_height_image+20

                if len(message) == 3:
                    message.append(new_height_image + 20)
                else:
                    message[3] = new_height_image+20

                if message[0] == 'me':
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

        self.screen.blit(pygame.font.Font(None, 30).render(str(self.friend), True, (0, 0, 0)), (450, 20))

        for box in boxes:
            box.draw(self.screen)

        pygame.display.flip()

    def save(self):
        with open('saves' + self.username + '.pickle', 'wb') as handle:
            pickle.dump(self.conv, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def handle_message(self):
        try:
            while True:
                data = q.get(False).split('|')

                if data[0] == 'msg':

                    text = resize_text(data[3]) if data[2] == 'txt' else data[3]

                    if str(data[1]) in self.conv:
                        self.conv[str(data[1])].append(['friend', data[2], text])
                    else:
                        self.conv[str(data[1])] = [['friend',  data[2], text]]

                    self.save()

        except Empty:
            pass

    def scroll_message(self, event, offset):

        height_top_message = 0

        for message in self.conv[str(self.friend)]:
            height_top_message += 20 * len(message[2]) + 20 if message[1] == 'txt' else 400

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 5 and offset >= 710:
                offset -= 35
            elif event.button == 4 and offset - height_top_message < 400:
                offset += 35
        return offset

    def main_window(self):
        message_box = InputBox(500, 745, 600, 45, round_box=12, color=(44, 221, 41),
                               color_text=(50, 50, 50), offset=(15, 12), size_text=28)
        send_button = Button(1130, 750, 50, 35, 'send', (0, 170, 0), (0, 200, 0), 25, offset='centered')
        friend_box = InputBox(20, 120, 360, 60, round_box=6, color=(44, 221, 41), color_text=(50, 50, 50))
        friend_button = Button(20, 200, 100, 50, 'choose', (0, 170, 0), (0, 200, 0), 25, offset='centered')
        img_button = Button(430, 745, 50, 45, 'img')

        boxes = [message_box, send_button, friend_box, friend_button, img_button]
        height = 710
        enter_key = None

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)

                for box in boxes:
                    enter_key = box.handle_event(event)
                    if enter_key:
                        break

                height = self.scroll_message(event, height)

            self.handle_message()

            if img_button.active:
                img_button.active = False
                self.send_message(obj_base64string, 'image')

            if (send_button.active or enter_key) and message_box.text:
                self.send_message(message_box.text, 'txt')
                send_button.active = False  # reset button
                message_box.text = ''  # reset box text

            if friend_button.active and friend_box.text:
                self.friend = friend_box.text
                if self.friend not in self.conv:
                    self.conv[self.friend] = []

            self.draw_main_window(boxes, height)


main = Main()
main.login()
