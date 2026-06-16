# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import utils
import math

class Swish(pg.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        # Load the swish animation
        self.frames = utils.load_animation('./assets/attacks/swish.png', 16, 16)
        self.frame = 0
        self.anim_speed = 30
        self.player = player
        self.image = self.frames[0]
        self.direction = player.direction
        self.rect = self.image.get_rect()
        offset = 24 if self.direction == 1 else -24
        self.rect.center = (self.player.rect.centerx + offset, self.player.rect.centery)

    def update(self, dt):
        # Follow the player's position
        self.frame += dt * self.anim_speed
        
        if self.frame >= len(self.frames):
            self.kill() # Remove swish when animation ends
            return

        self.image = self.frames[math.floor(self.frame)]
        if self.direction == -1: self.image = pg.transform.flip(self.image, True, False) # Flip image is facing left.

        # Position the swish in front of the player
        offset = 32 if self.direction == 1 else -32
        self.rect.center = (self.player.rect.centerx + offset, self.player.rect.centery)

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))

class Bomb(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, vel_x=0, vel_y=0):
        super().__init__()

        # Visuals
        self.animation = utils.load_animation('./assets/attacks/bomb.png', width, height)
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animation[self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Physics
        self.pos = pg.math.Vector2(self.rect.topleft)
        self.velocity = pg.math.Vector2(vel_x, vel_y)
        self.gravity = 0.8
        self.friction = 0.95
        self.on_ground = False

    def handle_collisions(self, collision_group, axis):
        for tile in collision_group:
            if self.rect.colliderect(tile.rect):
                if axis == 'horizontal':
                    if self.velocity.x > 0: self.rect.right = tile.rect.left
                    if self.velocity.x < 0: self.rect.left = tile.rect.right
                    self.pos.x = self.rect.x
                elif axis == 'vertical':
                    if self.velocity.y > 0:
                        self.rect.bottom = tile.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                    elif self.velocity.y < 0:
                        self.rect.top = tile.rect.bottom
                        self.velocity.y = 0
                    self.pos.y = self.rect.y

    def update(self, dt, collision_group):
        if self.on_ground:
            self.kill()
            return Explosion(self.rect.x, self.rect.y, 32, 32)

        # Physics
        self.velocity.x *= self.friction
        self.pos.x += self.velocity.x * (dt * 60)
        self.rect.x = round(self.pos.x)
        self.handle_collisions(collision_group, 'horizontal')

        self.on_ground = False
        self.velocity.y += self.gravity
        self.pos.y += self.velocity.y * (dt * 60)
        self.rect.y = round(self.pos.y)
        self.handle_collisions(collision_group, 'vertical')

        # Animate
        self.frame_index = (self.frame_index + self.animation_speed * (dt * 60)) % len(self.animation)
        self.image = self.animation[int(self.frame_index)]

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))

class Explosion(pg.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()

        # Visuals
        self.animation = [pg.transform.scale2x(i) for i in utils.load_animation('./assets/attacks/explosion.png', width, height)]
        self.frame_index = 0
        self.animation_speed = 0.2
        self.image = self.animation[self.frame_index]
        self.rect = self.image.get_rect(topleft=(x-width//2, y-height))

        # SFX
        explode_sfx = pg.mixer.Sound('./assets/sfx/explosion.ogg')
        explode_sfx.set_volume(0.5)
        explode_sfx.play()

    def update(self, dt):
        # Animate
        self.frame_index = (self.frame_index + self.animation_speed * (dt * 60))
        if self.frame_index > len(self.animation):
            self.kill()
            return
        self.image = self.animation[int(self.frame_index)]

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))