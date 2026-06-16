# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import math
import utils
from attacks import Swish

class Player(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((32, 32))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.is_grounded = False
        self.has_double_jump = False
        self.coins = 0
        self.kills = 0
        
        # Attack State
        self.is_attacking = False
        self.attack_duration = 0.3 
        self.attack_timer = 0
        self.swish_group = pg.sprite.Group()

        # Death State
        self.is_dead = False

        # Animations
        self.anim = {
            'idle': utils.load_animation('./assets/player/idle.png', 16, 16),
            'run': utils.load_animation('./assets/player/run.png', 16, 16),
            'jump_double': utils.load_animation('./assets/player/jump-double.png', 16, 16),
            'jump_up': utils.load_animation('./assets/player/jump-up.png', 16, 16),
            'jump_down': utils.load_animation('./assets/player/jump-down.png', 16, 16),
            'attack': utils.load_animation('./assets/player/attack.png', 16, 16),
            'die': utils.load_animation('./assets/player/die.png', 16, 16)
        }
        self.current_anim = 'idle'
        self.anim_speed = 10
        self.direction = 1
        self.frame = 0

        # SFX
        self.sfx = {
            'coin': pg.mixer.Sound('./assets/sfx/coin.ogg'),
            'death': pg.mixer.Sound('./assets/sfx/death.ogg'),
            'jump': pg.mixer.Sound('./assets/sfx/jump.ogg')
        }

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.attack_duration
            self.set_animation('attack', override=True)
            
            # Spawn swish
            swish = Swish(self)
            self.swish_group.add(swish)

    def update(self, dt, keys, collision_group, danger_group, level_info, enemy_group, boss):
        # If dead, only do gravity and animations
        if self.is_dead:
            self.vel_y += 32
            self.rect.y += self.vel_y * dt
            
            # Check if animation finished to reset level
            self.frame += dt * self.anim_speed
            if self.frame >= len(self.anim['die']):
                return "dead" # Signal to main loop to restart level
            
            # Update image for death frames
            frames = self.anim['die']
            self.image = frames[math.floor(self.frame) % len(frames)]
            if self.direction == -1:
                self.image = pg.transform.flip(self.image, True, False)
            
            # Swish Animations
            self.swish_group.update(dt)

            return
        
        # Update Attack Timer
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False

        # Horizontal Movement
        RIGHT = keys[pg.K_RIGHT] or keys[pg.K_d]
        LEFT = keys[pg.K_LEFT] or keys[pg.K_a]
        dx = (RIGHT - LEFT) * 256

        self.rect.x += dx * dt
        if dx != 0: self.direction = 1 if dx > 0 else -1
        
        for t in collision_group:
            if self.rect.colliderect(t.rect):
                if dx > 0: self.rect.right = t.rect.left
                if dx < 0: self.rect.left = t.rect.right

        # Vertical Movement & Gravity
        self.vel_y += 32
        self.rect.y += self.vel_y * dt
        
        for t in collision_group:
            if self.rect.colliderect(t.rect):
                if self.vel_y > 0:
                    self.rect.bottom = t.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = t.rect.bottom
                    self.vel_y = 0

        # Grounding Check
        self.is_grounded = False
        bottom_check = self.rect.copy()
        bottom_check.y += 1 
        for t in collision_group:
            if bottom_check.colliderect(t.rect):
                self.is_grounded = True
                self.has_double_jump = False
                break
        
        # Determine Animation State
        # If attacking, animation is attack,
        # If in the air and falling, animation is jump down.
        # If on the ground and moving, animation is run, otherwise idle.
        # Other animations are handled elsewhere.
        if self.is_attacking: self.set_animation('attack')
        elif not self.is_grounded:
            if self.vel_y > 16: self.set_animation('jump_down', True)
        else:
            if dx != 0: self.set_animation('run')
            else: self.set_animation('idle')
        
        # Check if Colliding with Enemy or Boss
        # If so, the player dies.
        for e in enemy_group: 
            if self.rect.colliderect(e.rect): self.die()

        if boss is not None and boss.hp > 0:
            if self.rect.colliderect(boss.rect): self.die()

        # Check if Colliding with a Danger Tile
        # If so, the player dies.
        for d in danger_group: 
            if self.rect.colliderect(d.rect): self.die()

        # Finishing Steps
        self.swish_group.update(dt)
        self.rect.x = max(0, min(level_info.tilewidth*(level_info.width-1), self.rect.x))
        self.animate(dt)

    def set_animation(self, name, override = False):
        # Prevent movement animations from overriding the attack
        if self.is_attacking and name != 'attack' and not override:
            return
        if not override and (self.current_anim in ['jump_up', 'jump_double', 'jump_down'] and self.vel_y > 0):
            return
        if self.current_anim != name:
            self.current_anim = name
            self.frame = 0

    def jump(self):
        if self.is_grounded or self.has_double_jump:
            if self.is_grounded:
                self.has_double_jump = True
                self.set_animation('jump_up', True)
            else:
                self.has_double_jump = False
                self.set_animation('jump_double', True)
            self.vel_y = -640
            self.is_grounded = False
            self.sfx['jump'].play()

    def animate(self, dt):
        self.frame += dt * self.anim_speed
        frames = self.anim[self.current_anim]
        self.image = frames[math.floor(self.frame) % len(frames)]
        if self.direction == -1:
            self.image = pg.transform.flip(self.image, True, False)

    def draw(self, screen, camera):
        # Draw player
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))
        # Draw active swish effects
        for swish in self.swish_group: swish.draw(screen, camera)

    def collect_coin(self):
        self.coins += 1
        self.sfx['coin'].play()

    def die(self):
        """Trigger the death state."""
        if not self.is_dead:
            self.is_dead = True
            self.vel_y = -400 # Small "hop" when dying (classic platformer style)
            self.current_anim = 'die'
            self.frame = 0
            self.sfx['death'].play() # Play death SFX