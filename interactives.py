import math
import pyperclip  # used for copy/paste
import pygame

pygame.init()


class InputBox:

    def __init__(self, x, y, w, h, password=False, hint='', offset=(10, 20), color=pygame.Color('lightskyblue3'),
                 color2=pygame.Color('dodgerblue2'), color_text=(30, 30, 30), round_box=0, size_text=35, size_hint=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.w = w
        self.color = color
        self.size_text = size_text
        self.color2 = color2
        self.color_text = color_text
        self.text = ''
        self.hint = hint
        self.password = password
        self.active = False
        self.offset = offset
        self.txt_surface = None
        self.round_box = round_box
        self.size_hint = size_hint if size_hint else size_text

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:

            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):

                # if the user click on the box, the box change it's state to True
                self.active = True

            else:
                # if the user click somewhere else:
                self.active = False

        if event.type == pygame.KEYDOWN and self.active:
            # handle the typing

            if event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.text += pyperclip.paste()

            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            elif event.key == pygame.K_RETURN:
                return 'send'

            else:
                self.text += event.unicode

            # Re-render the text.
            self.txt_surface = pygame.font.Font(None, self.size_text).render("*"*len(self.text) if self.password
                                                                             else self.text, True, self.color_text)

    def update(self):
        # Resize the box if the text is too long.
        width = max(self.w, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        if self.text:
            screen.blit(self.txt_surface, (self.rect.x+self.offset[0], self.rect.y+self.offset[1]))
        else:
            screen.blit(pygame.font.Font(None, self.size_hint).render(self.hint, True, self.color_text),
                        (self.rect.x+10, self.rect.y+10))

        # Blit the rect.
        pygame.draw.rect(screen, self.color if self.active else self.color2, self.rect, 2, self.round_box)

    def get_text(self):
        return self.text


class Button:
    def __init__(self, x, y, width=100, height=30, text='',
                 color=(170, 0, 0), color2=(255, 0, 0),
                 size_text=32, offset=(5, 5), image=None,
                 color_text=None, stroke=2, shape='rect',
                 radius=None) -> None:

        # image is a pygame.surface type
        self.rect        = pygame.Rect(x, y, width, height)
        self.x, self.y   = x, y
        self.shape       = shape
        self.radius      = radius
        self.stroke      = stroke
        self.color1      = color
        self.color2      = color2
        self.color       = color
        self.text        = text
        self.active      = False
        self.size_text   = size_text
        self.image       = image

        if text:
            self.txt_surface = pygame.font.Font(None, size_text).render(text, True, color_text if color_text else color)

            if offset == 'centered':
                self.offset_x = (width-self.txt_surface.get_width())/2
                self.offset_y = (height-self.txt_surface.get_height())/2
            elif offset[0] == 'centered':
                self.offset_x = (width-self.txt_surface.get_width())/2
                self.offset_y = offset[1]
            elif offset[1] == 'centered':
                self.offset_x = offset[0]
                self.offset_y = (height-self.txt_surface.get_height())/2
            else:
                self.offset_x, self.offset_y = offset

    def handle_event(self, event):
        self.active = False

        x, y = pygame.mouse.get_pos()
        if (self.shape == 'rect' and self.rect.collidepoint((x, y))) or \
                (self.shape == 'circle' and math.sqrt((x-self.x)**2+(y-self.y)**2) < self.radius):

            if event.type == pygame.MOUSEBUTTONUP:
                self.active = True
            self.color = self.color2
        else:
            self.color = self.color1

    def draw(self, screen):
        if not self.image:
            # Blit the text.
            screen.blit(self.txt_surface, (self.rect.x+self.offset_x, self.rect.y+self.offset_y))

            # Blit the rect.
            if self.shape == 'rect':
                pygame.draw.rect(screen, self.color, self.rect, self.stroke)
            else:
                pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius, self.stroke)
        else:
            # else blit the image
            screen.blit(self.image, (self.rect.x, self.rect.y))


class BigInputBox:
    def __init__(self, x, y, w, h, offset=(10, 20)):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = ['| ']
        self.active = False
        self.offset = offset

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = pygame.Color('dodgerblue2') if self.active else pygame.Color('lightskyblue3')
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    if self.text[-1]:
                        self.text[-1] = self.text[-1][:-1]
                    elif len(self.text) > 1:
                        self.text.remove(self.text[-1])
                elif event.key == pygame.K_RETURN:
                    self.text.append('| ')
                else:
                    self.text[-1] += event.unicode
                    self.update()
                # Re-render the text.

        self.txt_surface = pygame.font.Font(None, 30).render(self.text[-1][1:], True, self.color)

    def update(self):
        # width = max(200, self.txt_surface.get_width()+10)
        # self.rect.w = width
        if self.txt_surface.get_width() > 395:
            ind = len(self.text[-1]) - self.text[-1][::-1].index(' ')
            self.text.append(str(self.text[-1][ind-1:]))
            self.text[-2] = self.text[-2][:ind]

    def draw(self, screen):
        # Blit the text.
        for row in self.text:
            if row != '|  ':
                screen.blit(pygame.font.Font(None, 30).render(row[1:], True, self.color), (self.rect.x+self.offset[0], self.rect.y+self.offset[1]+25*self.text.index(row)))
            else:
                self.text.remove(row)

        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_text(self):
        return self.text
