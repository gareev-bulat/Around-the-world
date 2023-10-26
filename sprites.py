import pygame as pg
import settings
import sqlite3
from random import choice
import os, sys
from pygame import time


# загрузка изображений
def load_image(name, colorkey=None):
    fullname = name
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pg.image.load(fullname)
    return image


# обрезка
def cut_sheet(sheet, columns, rows, frames):
    rect = pg.Rect(0, 0, sheet.get_width() // columns,
                        sheet.get_height() // rows)
    for j in range(rows):
        for i in range(columns):
            frame_location = (rect.w * i, rect.h * j)
            frames.append(pg.transform.scale(sheet.subsurface(pg.Rect(
                frame_location, rect.size)), (64, 64)))

# враги
class Enemies(pg.sprite.Sprite):
    def __init__(self, game, x, y, tip):
        pg.mixer.init()
        self.groups = game.enemies
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.clock = pg.time.Clock()
        self.frames = []
        self.first_count = 0
        self.second_count = 0
        self.vx, self.vy = 0, 0
        self.make_jump = False
        self.vniz = False
        self.onLadder = False
        self.jump_counter = 50
        self.levitating = 0
        self.tip = tip
        if self.tip == 'bat':
            self.x = x
            self.y = y
            cut_sheet(load_image("EnemyBatLeft.png"), 3, 1, self.frames)
            cut_sheet(load_image("EnemyBatRight.png"), 3, 1, self.frames)
            self.image = self.frames[3]
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
        self.do()


# игрок
class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        pg.mixer.init()
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.money_music = pg.mixer.Sound('picking a coin.mp3')
        self.player_damage_music = pg.mixer.Sound('hit_player.mp3')
        self.healing_player_music = pg.mixer.Sound('healing_player.mp3')
        self.money_music.set_volume(1.0)
        self.game = game
        self.clock = pg.time.Clock()
        self.first_count = 0
        self.second_count = 0
        if settings.active_skin == 'black':
            self.frames = []
            cut_sheet(load_image("testPersonRight.png"), 4, 1, self.frames)
            cut_sheet(load_image("testPersonLeft.png"), 4, 1, self.frames)
            cut_sheet(load_image("testPersonClimb.png"), 4, 1, self.frames)
        elif settings.active_skin == 'orange':
            self.frames = []
            cut_sheet(load_image("testPersonRightOrange.png"), 4, 1, self.frames)
            cut_sheet(load_image("testPersonLeftOrange.png"), 4, 1, self.frames)
            cut_sheet(load_image("testPersonClimbOrange.png"), 4, 1, self.frames)
        self.image = self.frames[4]
        self.rect = self.image.get_rect()
        self.vx, self.vy = 0, 0
        self.make_jump = False
        self.vniz = False
        self.onLadder = False
        self.extraLadder = False
        self.temp = []
        self.jump_counter = 50
        self.levitating = 0
        self.count_damage_shipps = 0
        self.money_counter = 50
        self.rotation = 'left'
        self.x = x
        self.y = y
        self.con = sqlite3.connect("database.db")

    def work_with_base(self):
        cur = self.con.cursor()
        result = cur.execute("""SELECT * FROM money_counter""").fetchall()
        return str(result[0][0])

    def get_keys(self):
        hits_with_ladders = pg.sprite.spritecollide(self, self.game.ladders, False)
        hits_with_money = pg.sprite.spritecollide(self, self.game.money, False)
        hits_with_shipp = pg.sprite.spritecollide(self, self.game.shipp, False)
        hits_with_medthings = pg.sprite.spritecollide(self, self.game.medthings, False)
        hits_with_liquid = pg.sprite.spritecollide(self, self.game.liquid, False)
        if len(hits_with_money) != 0:
            hits_with_money[0].kill()
            settings.MONEY_COUNTER += len(hits_with_money)
            self.sounds('coin')
        if len(hits_with_ladders) != 0:
            self.onLadder = True
        else:
            self.onLadder = False
        if len(hits_with_liquid) != 0:
            settings.HEALTH = 0
        if len(hits_with_shipp) != 0:
            self.count_damage_shipps = round(self.count_damage_shipps + 0.0625, 4)
            for hit in hits_with_shipp:
                if self.count_damage_shipps == 0.25 or self.count_damage_shipps % 1 == 0:
                    settings.HEALTH -= settings.ENEMIES_DAMAGE['shipp']
                    self.sounds('damage_to_player')
                    if self.rotation == 'left':
                        for i in range(560):
                            self.x += 0.15 / 2
                            self.y -= 0.15 / 2
                    else:
                        for i in range(560):
                            self.x -= 0.15 / 2
                            self.y -= 0.15 / 2
        elif len(hits_with_shipp) == 0:
            self.count_damage_shipps = 0
        if hits_with_medthings:
            self.sounds('medthings')
            settings.HEALTH = hits_with_medthings[0].health_plus + settings.HEALTH
            hits_with_medthings[0].kill()
            if settings.HEALTH > 1.0:
                settings.HEALTH = 1.0
        self.vx, self.vy = 0, 0
        keys = pg.key.get_pressed()
        mods = pg.key.get_mods()
        if (keys[pg.K_LEFT] and not keys[pg.K_RIGHT]) or (keys[pg.K_a] and not keys[pg.K_d]):
            if self.make_jump:
                self.image = self.frames[4]
            if not self.make_jump:
                self.first_count = round(self.first_count + 0.25, 2)
                if int(self.first_count) == self.first_count:
                    self.image = self.frames[4:8][int(self.first_count) % 4]
            self.rotation = 'left'
            self.vx = -settings.PLAYER_SPEED
        if (keys[pg.K_RIGHT] and not keys[pg.K_LEFT]) or (keys[pg.K_d] and not keys[pg.K_a]):
            if self.make_jump:
                self.image = self.frames[0]
            self.vx = settings.PLAYER_SPEED
            if not self.make_jump:
                self.second_count = round(self.second_count + 0.25, 3)
                if int(self.second_count) == self.second_count:
                    self.image = self.frames[:4][int(self.second_count) % 4]
            self.rotation = 'right'
        if self.onLadder:
            if 1 <= self.rect.bottom - hits_with_ladders[0].rect.top <= 10:
                self.levitating = 0
                self.extraLadder = True
            else:
                self.levitating = 5
                self.extraLadder = False
            if keys[pg.K_UP] or keys[pg.K_w] and not self.extraLadder:
                self.y = self.y - 10
                self.first_count += 0.25
            self.image = self.frames[8:12][int(self.first_count) % 4]
        else:
            self.extraLadder = False
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.vy = settings.PLAYER_SPEED
        if mods & pg.KMOD_SHIFT and (keys[pg.K_LEFT] or keys[pg.K_a]):
            self.vx = -settings.PLAYER_SPEED - 150
        if mods & pg.KMOD_SHIFT and (keys[pg.K_RIGHT] or keys[pg.K_d]):
            self.vx = settings.PLAYER_SPEED + 150
        if (keys[pg.K_SPACE] or keys[pg.K_UP]) and self.make_jump is False and self.onLadder is False:
            self.make_jump = True
            choice(self.game.jump_sound).play()
        if self.vx != 0 and self.vy != 0:
            self.vx = self.vx // 1.5
            self.vy = self.vy // 1.5

    def jump(self):
        if self.onLadder is False:
            hits_with_walls = pg.sprite.spritecollide(self, self.game.walls, False)
            if self.jump_counter >= -50:
                self.y = self.y - self.jump_counter / 2.5
                self.jump_counter -= 1
            else:
                self.jump_counter = 50
                self.make_jump = False

    def collide_with_walls(self, direction):
        hits_with_walls = pg.sprite.spritecollide(self, self.game.walls, False)

        try:
            if self.rect.bottom - 1 == hits_with_walls[0].rect.top or self.rect.bottom - 10 == hits_with_walls[0].rect.top:
                self.make_jump = False
                self.jump_counter = 50
        except IndexError:
            pass

        if direction == 'x':
            if hits_with_walls:
                if self.vx < 0:
                    self.x = hits_with_walls[0].rect.right
                if self.vx > 0:
                    self.x = hits_with_walls[0].rect.left - self.rect.width
                self.vx = 0
                self.rect.x = self.x
        if direction == 'y':
            if hits_with_walls:
                if self.vy < 0 or self.jump_counter >= 0:
                    self.y = hits_with_walls[0].rect.bottom
                if self.vy > 0 or self.jump_counter <= 0:
                    self.y = hits_with_walls[0].rect.top - self.rect.height
                if self.vy == 0 and not self.make_jump and hits_with_walls[0].rect.top > self.rect.top:
                    self.y = hits_with_walls[0].rect.top - self.rect.height
                if (self.vy == 0 or self.vy > 0) and hits_with_walls[0].rect.top <= self.rect.top:
                    self.y = hits_with_walls[0].rect.bottom
                self.vy = 0
                self.levitating = 0
                self.rect.y = self.y
            elif not self.extraLadder:
                self.levitating = 5

    def sounds(self, what):
        if what == 'coin':
            self.money_music.play()
        if what == 'damage_to_player':
            self.player_damage_music.play()
        if what == 'medthings':
            self.healing_player_music.play()

    def update(self):
        self.y = self.y + self.levitating
        self.get_keys()
        if self.make_jump:
            self.jump()
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        self.collide_with_walls('x')
        self.rect.y = self.y
        self.collide_with_walls('y')


# жидкость
class Liquid(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.liquid
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

#стены, платформы
class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

#лестница
class Ladder(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.ladders
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

#монетки
class Money(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.money
        pg.sprite.Sprite.__init__(self, self.groups)
        image = load_image('money.png')
        self.image = pg.transform.scale(image, (32, 32))
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y


#аптечка
class MedKit(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.medthings
        pg.sprite.Sprite.__init__(self, self.groups)
        image = load_image('medkit.png')
        self.image = pg.transform.scale(image, (64, 64))
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.health_plus = 1.0
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

# бинт
class Bandage(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.medthings
        pg.sprite.Sprite.__init__(self, self.groups)
        image = load_image('bandage.png')
        self.image = pg.transform.scale(image, (48, 65))
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.health_plus = 0.2
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

# шипы
class Shipp(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.shipp
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

# меч
class Sword(pg.sprite.Sprite):
    def __init__(self, game, x, y, x1, y1):
        self.groups = game.sword
        self.player_x = game.player.x
        self.player_y = game.player.y
        pg.sprite.Sprite.__init__(self, self.groups)
        image = load_image('sword_2.jpg')
        self.image = pg.transform.scale(image, (120, 60))
        self.rect = pg.Rect(x, y, x1, y1)
        # self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        self.do()

    def do(self):
        self.rect.x = self.player_x
        self.rect.y = self.player_y


