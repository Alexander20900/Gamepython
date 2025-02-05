import csv
import os
import random
import pygame
import sys
from pygame.math import Vector2
from pygame.draw import rect

pygame.init()
size = width, height = 800, 600
screen = pygame.display.set_mode(size)

start = False

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

GRAVITY = Vector2(0, 0.86)


def load_image(name, colorkey=None):
    fullname = os.path.join('', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Player(pygame.sprite.Sprite):
    win: bool
    died: bool

    def __init__(self, image, platforms, pos, *groups):
        super().__init__(*groups)
        self.onGround = False  # игрок на земле?
        self.platforms = platforms
        self.died = False  # игрок умер?
        self.win = False  # игрок победил?

        self.image = pygame.transform.smoothscale(image, (32, 32))
        self.rect = self.image.get_rect(center=pos)
        self.jump_amount = 11  # длина прыжка
        self.particles = []
        self.isjump = False  # игрок прыгнул?
        self.vel = Vector2(0, 0)

    def draw_particle_trail(self, x, y, color=(255, 255, 255)):
        # частицы за игроком

        self.particles.append(
            [[x - 5, y - 8], [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
             random.randint(5, 8)])

        for particle in self.particles:
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[2] -= 0.5
            particle[1][0] -= 0.4
            rect(alpha_surf, color,
                 ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for i in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)

    def collide(self, yvel, platforms):
        global coins

        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, Orb) and (keys[pygame.K_UP] or keys[pygame.K_SPACE]):
                    pygame.draw.circle(alpha_surf, (255, 255, 0), p.rect.center, 18)

                    self.jump_amount = 13  # дополнительный прыжок от орба
                    self.jump()
                    self.jump_amount = 11  # возвращение обычного прыжка

                if isinstance(p, End):
                    self.win = True

                if isinstance(p, Spike):
                    self.died = True  # смерть от шипа

                if isinstance(p, Coin):
                    # отслеживает все монеты на протяжении всей игры(всего возможно 6)
                    coins += 1

                    p.rect.x = 0
                    p.rect.y = 0

                if isinstance(p, Platform):  # блоки

                    if yvel > 0:
                        self.rect.bottom = p.rect.top  # не даёт игроку провалиться под землю
                        self.vel.y = 0

                        # устанавливается значение true, потому что игрок столкнулся с землей
                        self.onGround = True

                        self.isjump = False
                    elif yvel < 0:
                        self.rect.top = p.rect.bottom
                    else:
                        self.vel.x = 0
                        self.rect.right = p.rect.left
                        self.died = True

    def jump(self):
        self.vel.y = -self.jump_amount

    def update(self):
        if self.isjump:
            if self.onGround:
                self.jump()

        if not self.onGround:
            self.vel += GRAVITY

            # макс скорость падения
            if self.vel.y > 100:
                self.vel.y = 100

        self.collide(0, self.platforms)

        self.rect.top += self.vel.y

        # игрок находится в воздухе, а если нет после столкновения он будет перевернут
        self.onGround = False

        self.collide(self.vel.y, self.platforms)

        eval_outcome(self.win, self.died)


class Draw(pygame.sprite.Sprite):

    def __init__(self, image, pos, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)


class Platform(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Spike(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Coin(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Orb(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Trick(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class End(Draw):

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


def init_level(map):
    # создание уровня из csv таблицы
    x = 0
    y = 0

    for row in map:
        for col in row:

            if col == "0":
                Platform(block, (x, y), elements)

            if col == "Coin":
                Coin(coin, (x, y), elements)

            if col == "-2":
                Spike(spike, (x, y), elements)
            if col == "-3":
                orbs.append([x, y])

                Orb(orb, (x, y), elements)

            if col == "T":
                Trick(trick, (x, y), elements)

            if col == "End":
                End(end, (x, y), elements)
            x += 32
        y += 32
        x = 0


def blitRotate(surf, image, pos, originpos: tuple, angle: float):
    w, h = image.get_size()
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]

    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    # рассчитать перевод оси
    pivot = Vector2(originpos[0], -originpos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    # вычислить верхнюю левую границу повернутого изображения
    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    # получить перевёрнутое изображение
    rotated_image = pygame.transform.rotozoom(image, angle, 1)

    # повернуть и отразить изображение
    surf.blit(rotated_image, origin)


def won_screen():
    global attempts, level, fill
    attempts = 0
    player_sprite.clear(player.image, screen)
    winscr = pygame.transform.scale(load_image('level-complete.png'), (width, height))
    screen.blit(winscr, (0, 0))
    if level == 0:
        txt_win1 = f"Coin{coins}/3!"
        txt_win = f"Вы прошли level 1! {txt_win1}"
        txt_wim2 = f"Нажмите пробел для продолжения или ESC чтобы выйти"
        won_game = font.render(txt_win, True, WHITE)
        screen.blit(won_game, (70, 150))
        won_game2 = font.render(txt_wim2, True, WHITE)
        screen.blit(won_game2, (70, 400))
    else:
        won_game = font.render("Вы прошли игру! Нажмите ESC чтобы выйти", True, WHITE)
        screen.blit(won_game, (50, 200))
        waiting = True
        while waiting:
            clock.tick(120)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        terminate()

    level += 1

    wait_for_key()
    reset()


def death_screen():
    global attempts, fill
    fill = 0
    player_sprite.clear(player.image, screen)
    attempts += 1
    game_over = font.render("Игра окончена. Нажмите пробел для рестарта", True, WHITE)
    orbyellow = pygame.image.load((os.path.join("images", "orb-yellow.png")))
    orbdes = font.render(" - При нажатии на орб происходит двойной прыжок", True, WHITE)
    spikeim = pygame.image.load((os.path.join("images", "obj-spike.png")))
    spikedes = font.render(" - При ударении о шип вы проигрываете", True, WHITE)
    coinim = pygame.image.load((os.path.join("images", "Coin.png")))
    coindes = font.render(" - Вы можете собрать монеты, проходя другими путями", True, WHITE)
    screen.fill(pygame.Color("black"))
    screen.blits(
        [[tip, (100, 500)], [orbyellow, (30, 30)], [orbdes, (155, 80)], [spikeim, (30, 170)], [spikedes, (155, 220)],
         [coinim, (10, 310)], [coindes, (155, 400)], [game_over, (100, 550)]])

    wait_for_key()
    reset()


def eval_outcome(won: bool, died: bool):
    if won:
        won_screen()
    if died:
        death_screen()


def block_map(level_num):
    lvl = []
    with open(level_num, newline='') as csvfile:
        trash = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in trash:
            lvl.append(row)
    return lvl


def start_screen():
    fon = pygame.transform.scale(load_image('fon2.png'), (width, height))
    screen.blit(fon, (0, 0))
    typ = font.render("Нажмите пробел для начала", True, BLACK)
    screen.blit(typ, (260, 400))


def reset():
    global player, elements, player_sprite, level

    if level == 1:
        pygame.mixer.music.load(os.path.join("music", "Base_After_Base.ogg"))
    pygame.mixer_music.play()
    player_sprite = pygame.sprite.Group()
    elements = pygame.sprite.Group()
    player = Player(avatar, elements, (150, 150), player_sprite)
    init_level(
        block_map(
            level_num=levels[level]))


def move_map():
    for sprite in elements:
        sprite.rect.x -= CameraX


def stats(surf, money=0):
    global fill
    progress_colors = [pygame.Color("red"), pygame.Color("orange"), pygame.Color("yellow"), pygame.Color("blue"),
                       pygame.Color("green")]

    tries = font.render(f" Attempt {str(attempts)}", True, WHITE)
    BAR_LENGTH = 600
    BAR_HEIGHT = 10
    fill += 0.2
    outline_rect = pygame.Rect(0, 0, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(0, 0, fill, BAR_HEIGHT)
    col = progress_colors[int(fill / 100)]
    rect(surf, col, fill_rect, 0, 4)
    rect(surf, WHITE, outline_rect, 3, 4)
    screen.blit(tries, (BAR_LENGTH, 0))


def wait_for_key():
    global level, start
    waiting = True
    while waiting:
        clock.tick(120)
        pygame.display.flip()

        if not start:
            start_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start = True
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    terminate()


def coin_count():
    global coins
    if coins > 3:
        coins = 3
    else:
        coins += 1
    return coins


def resize(img, size=(32, 32)):
    resized = pygame.transform.smoothscale(img, size)
    return resized


def terminate():
    pygame.quit()
    sys.exit()


font = pygame.font.SysFont("lucidaconsole", 17)
end = pygame.image.load(os.path.join("images", "bg.png"))
avatar = pygame.image.load(os.path.join("images", "avatar.png"))  # загрузка кубика
pygame.display.set_icon(avatar)
alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

player_sprite = pygame.sprite.Group()
elements = pygame.sprite.Group()

# изображения
spike = pygame.image.load(os.path.join("images", "obj-spike.png"))  # шип
spike = resize(spike)
coin = pygame.image.load(os.path.join("images", 'Coin.png'))  # монета
coin = pygame.transform.smoothscale(coin, (32, 32))
block = pygame.image.load(os.path.join("images", "block_1.png"))  # блок
block = pygame.transform.smoothscale(block, (32, 32))
orb = pygame.image.load((os.path.join("images", "orb-yellow.png")))  # орб
orb = pygame.transform.smoothscale(orb, (32, 32))
trick = pygame.image.load((os.path.join("images", "obj-breakable.png")))  # частицы орба
trick = pygame.transform.smoothscale(trick, (32, 32))

fill = 0
num = 0
CameraX = 0
attempts = 1
coins = 0
angle = 0
level = 0

particles = []
orbs = []
win_cubes = []

levels = ["level_1.csv", "level_2.csv"]
level_list = block_map(levels[level])
level_width = (len(level_list[0]) * 32)
level_height = (len(level_list) * 32)
init_level(level_list)

pygame.display.set_caption('Geometry Rush')

text = font.render('image', False, (255, 255, 0))

music = pygame.mixer_music.load(os.path.join("music", "Back_On_Track.ogg"))
pygame.mixer_music.play()

bg = pygame.image.load(os.path.join("images", "bg.png"))

player = Player(avatar, elements, (150, 150), player_sprite)

tip = font.render("Подсказка: чтобы прыгать можно нажать на пробел либо стрелку вверх", True, WHITE)
running = True
while running:
    keys = pygame.key.get_pressed()

    if not start:
        wait_for_key()
        reset()

        start = True

    player.vel.x = 6

    eval_outcome(player.win, player.died)
    if keys[pygame.K_UP] or keys[pygame.K_SPACE]:
        player.isjump = True

    alpha_surf.fill((255, 255, 255, 1), special_flags=pygame.BLEND_RGBA_MULT)

    player_sprite.update()
    CameraX = player.vel.x
    move_map()

    screen.blit(bg, (0, 0))  # очистить экран

    player.draw_particle_trail(player.rect.left - 1, player.rect.bottom + 2,
                               WHITE)
    screen.blit(alpha_surf, (0, 0))
    stats(screen, coin_count())

    if player.isjump:
        angle -= 9  # угол поворота кубика при прыжке
        blitRotate(screen, player.image, player.rect.center, (16, 16), angle)
    else:
        player_sprite.draw(screen)
    elements.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_2:
                player.jump_amount += 1

            if event.key == pygame.K_1:
                player.jump_amount -= 1

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
