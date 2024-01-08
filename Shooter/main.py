import pygame
import os
import random
import csv
from datetime import date 




pygame.init()


SCREEN_WIDTH =  900
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Contra at Home')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.4
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
time_stamp = date.today()


# player actions

moving_left = False
moving_right = False
shoot = False



#load images
#buttons
start_img = pygame.image.load('img\start_btn.png').convert_alpha()
exit_img = pygame.image.load('img\exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img\\restart_btn.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img\\tile\\{x}.png')
    img = pygame.transform.scale(img,(TILE_SIZE, TILE_SIZE))
    img_list.append(img)

#bullet
bullet_img = pygame.image.load('img\\bullet.png').convert_alpha()
#pick up medals and health
medal_img = pygame.image.load('img\\medal.png').convert_alpha()
health_img = pygame.image.load('img\\health.png')
item_boxes = {
    'Health'    : health_img,
    'Medal'     : medal_img
}



#defining colors
BG = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
WHITE = (255,255,255)
BLACK = (0,0,0)

# define font
font = pygame.font.SysFont('MS Gothic', 30)
big_font = pygame.font.SysFont('MS Gothic', 60)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)


# reset level funct
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data
    

   

class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.shoot_cooldown = 0
        self.health = 100
        self.max_health = self.health
        self.score = 0
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = [] #store sprites
        self.frame_index = 0 #start with sprite number 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        #create ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idle_counter = 0
        
        #load all images for the players
        animation_types = ['idle', 'walk', 'jump', 'death']
        for animation in animation_types:
            #reset temporary list of images
            temp_list = []
            #count number of files in the folder
            num_of_frames = len(os.listdir(f'img\{self.char_type}\{animation}'))
            for image in range(num_of_frames):
                img = pygame.image.load(f'img\{self.char_type}\{animation}\{animation}_{image}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width()* scale), int(img.get_height()*scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        #reset movement vars
        screen_scroll = 0
        dx = 0
        dy = 0

        # movement variables if moving
        if moving_left:
            dx = -self.speed   
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        #jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        #apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y 
        dy += self.vel_y

        #check collision with floor
        for tile in world.obstacle_list:
            #check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai hits a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
        #check for collision in the y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if i am below the ground, i.e jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        #check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        #check for collition with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        #check if fall off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0
        # check if going off the edges of the screen
        if self.char_type == 'lance':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #update rect position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on players position
        if self.char_type == 'lance':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH < (world.level_length * TILE_SIZE )- SCREEN_WIDTH)\
                or (self.rect.left < SCROLL_THRESH ):
                self.rect.x -= dx
                screen_scroll = -dx
       
        return screen_scroll, level_complete
    
    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 300) == 1:
                self.update_action(0)#0 is idle
                self.idling = True
                self.idle_counter = 50
            #check if the ai is near the player
            if self.vision.colliderect(player.rect):
                #stop running and face player
                self.update_action(0)# 0 is idle
                #shoot
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1 is walk
                    self.move_counter += 1
                    #update ai vision as the enemy moves
                    self.vision.center=(self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #pygame.draw.rect(screen,RED, self.vision) # to see the area of vision

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idle_counter -= 1
                    if self.idle_counter <= 0:
                        self.idling = False

        #scroll
        self.rect.x += screen_scroll

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 15
            bullet = Bullet(self.rect.centerx + (
                0.85 * self.rect.size[0] * self.direction), self.rect.centery +(-0.25 * self.rect.size[0]), self.direction)
            bullet_group.add(bullet)


    def update_animation(self):
        #update the animations
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.image =  self.animation_list[self.action][self.frame_index]
        # check is enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index+= 1
        # if the folder is out of frames, reset back to start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3: # 3 is death
                self.frame_index =len(self.animation_list[self.action]) - 1
            else:    
                self.frame_index = 0

    def update_action(self, new_action):
        #check if the new action is different than the previous one
        if new_action != self.action:
            self.action = new_action
            #update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
        


    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
    def __init__(self):
        self.obstacle_list = []
    
    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile == 9 or tile == 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15: #create player
                        player = Soldier('lance',x * TILE_SIZE+50, y * TILE_SIZE, 1.65, 4)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16: #create enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2)
                        enemy_group.add(enemy)
                    elif tile == 17: #create medal box
                        item_box = ItemBox('Medal',x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18: #create health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:# exit of the level
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar    

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action
    
class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)    
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)    
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)    
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if the PLAYER has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #check what kind of medal it was
            if self.item_type == 'Health':
                player.health += 25
                player.score += 100
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Medal':
                player.score += 1000
        #delete item
            self.kill()

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #update with new health
        self.health = health
        #calc health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150* ratio, 20))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.direction = direction

    def update(self):

        #move bullets
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #check if bullet has gone off screen
        if self.rect.right < 0  or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #check collision with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 10
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 34
                    self.kill()
                    if enemy.health >= 0:
                        player.score += 200
#create and store high score
if os.path.exists('score.txt'):
    with open('score.txt', 'r') as file:
        high_score = int(file.read())
        
else:
    high_score = 0


#create buttons
start_button = Button(SCREEN_WIDTH // 2-130,SCREEN_HEIGHT // 2 - 150, start_img, 1 )
exit_button = Button(SCREEN_WIDTH // 2-110,SCREEN_HEIGHT // 2 + 50, exit_img, 1 )
restart_button = Button(SCREEN_WIDTH // 2-100,SCREEN_HEIGHT // 2 - 50, restart_img, 1 )
#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

run = True
while run:

    clock.tick(FPS)
    if start_game == False:
        #main menu
        screen.fill(BG)
        #add buttons
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
        
    else:
            
        #update background
        draw_bg()
        #draw map
        world.draw()

        #show player health
        health_bar.draw(player.health)

        # show health
        draw_text(f'HIGH SCORE: {high_score} on {time_stamp}', font, WHITE, 400, 35 )
        draw_text(f'HEALTH: {player.health}', font, WHITE, 10, 35)
        draw_text(f'SCORE: {player.score}', font, WHITE, 200, 35)
        
        player.update()
        player.draw()

        
        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        #update and draw groups
        bullet_group.update()
        bullet_group.draw(screen)
        item_box_group.update()
        item_box_group.draw(screen)
        decoration_group.update()
        decoration_group.draw(screen)
        water_group.update()
        water_group.draw(screen)
        exit_group.update()
        exit_group.draw(screen)



        # update player actions
        if player.alive:
            #shoot
            if shoot:
                player.shoot()

            if player.in_air:
                player.update_action(2) #2 is jump
            elif moving_left or moving_right:
                player.update_action(1) #1 is running
            else:
                player.update_action(0) #0 is idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            #check if player has completed the level
            if level_complete:
                draw_text('YOU WIN!!!', big_font, RED, SCREEN_WIDTH // 2-170,SCREEN_HEIGHT // 2 - 150)
                if player.score > high_score:
                    high_score = player.score
                    with open('score.txt', 'w') as file:
                        file.write(str(high_score))
                if restart_button.draw(screen):
                    world_data = reset_level()
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)

        else:

            screen_scroll = 0
            if player.score > high_score:
                high_score = player.score
                with open('score.txt', 'w') as file:
                    file.write(str(high_score))
            if restart_button.draw(screen):
                world_data = reset_level()
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)






    for event in pygame.event.get():
        #quit game
        if event.type == pygame.QUIT:
            run = False
            
        if event.type == pygame.KEYDOWN: # Keyboard presses
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False


        if event.type == pygame.KEYUP: # Keyboard releases
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            

    pygame.display.update()
