# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import utils
from attacks import Bomb
from enemy import Enemy
from particles import Particle
import random

class Boss(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, speed=2):
        super().__init__()

        # Visuals
        self.animations = {
            'idle': utils.load_animation('./assets/boss/idle.png', width, height),
            'run':  utils.load_animation('./assets/boss/run.png', width, height),
            'hit':  utils.load_animation('./assets/boss/hit.png', width, height)
        }
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))

        # HP and Hit Time
        self.max_hp = 7
        self.hp = self.max_hp
        self.hit_time = 0
        self.stun_time = 0.2
        
        # Physics
        self.pos = pg.math.Vector2(self.rect.topleft)
        self.velocity = pg.math.Vector2(0, 0)
        self.speed = speed
        self.gravity = 0.8
        self.jump_speed = -14
        self.on_ground = False
        self.flip = False

        # State Machine
        self.states = {
            "idle": self.state_idle,
            "chase": self.state_chase,
            "musket": self.state_musket,
            "bomb": self.state_bomb,
            "hit": self.state_hit
        }
        self._state = "idle"

        # Battle Started and Detection
        self.battle_started = False
        self.detection_range = 200

        # Chase Duration
        self.time_since_chase_began = 0

        # Bomb State Values
        self.bomb_cooldown = 0
        self.bombs_thrown = 0

        # Musket State Variables
        self.musket_image = pg.image.load('./assets/boss/musket.png').convert_alpha()
        self.musket_rect = self.musket_image.get_rect(topleft=(x, y+5))
        self.musket_image_r = self.musket_image
        self.musket_rect_r = self.musket_rect
        self.musket_hit_point = None
        self.musket_aim_time = 0.5 # Time to aim for
        self.musket_aim_timer = self.musket_aim_time
        self.musket_aimed = False # Has the current musket shot been aimed
        self.musket_warn_time = 0.25 # Time to warn for
        self.musket_warn_timer = self.musket_warn_time
        self.musket_warned = False # Has the warn delay for the current musket shot occured

        # Child Sprites
        self.bomb_group = pg.sprite.Group()
        self.explosion_group = pg.sprite.Group()
        self.particle_group = pg.sprite.Group()
        self.minion_cooldown = 5 # Don't allow minion spawning until 5 seconds into the fight.

        # SFX and Background Track
        self.hit_sfx = pg.mixer.Sound('./assets/sfx/hit.ogg')
        self.shoot_sfx = pg.mixer.Sound('./assets/sfx/musket-shoot.ogg')
        self.bg_track = pg.mixer.Sound('./assets/sfx/boss-music.ogg')

    @property
    def state(self): return self._state

    @state.setter
    def state(self, value):
        # If state is being set to chase, reset the chase timer.
        if value == "chase": self.time_since_chase_began = 0
        # Reset musket valeus in setting state to musket
        elif value == "musket":
            self.musket_aimed = False
            self.musket_warned = False
            self.musket_aim_timer = self.musket_aim_time
            self.musket_warn_timer = self.musket_warn_time
            self.musket_hit_point = None
        # Choose a random state if random is selected
        elif value == "random":
            choices = ["chase", "musket", "bomb"]
            try: choices.remove(self.state) # When selecting a random state, don't choose the current one.
            except ValueError: pass # If the state is not in choices ('idle' or 'hit'), just ignore it.

            if self.state == 'hit': # When selecting a random state after a hit, don't select chase again.
                try: choices.remove('chase')
                except ValueError: pass
            self.state = random.choice(choices)
            return # Exit before we set the state to the value parameter

        # Set the state to the value parameter
        self._state = value

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

    def state_idle(self, player, dt, collision_group):
        self.velocity.x = 0
        dist_sq = (player.rect.centerx - self.rect.centerx)**2 + (player.rect.centery - self.rect.centery)**2
        
        if not self.battle_started and dist_sq < self.detection_range**2:
            self.bg_track.play(loops=-1)
            self.battle_started = True
            self.state = "chase" # Always start boss battle by chasing player

    def state_chase(self, player, dt, collision_group):
        self.time_since_chase_began += dt
        dist_x = player.rect.centerx - self.rect.centerx
        self.velocity.x = self.speed if dist_x > 0 else -self.speed

        # Switch State Logic
        if self.time_since_chase_began >= 3:
            self.state = "random"

        # Jump Logic
        if self.on_ground:
            probe_offset = 25 if self.velocity.x > 0 else -25
            probe_rect = pg.Rect(self.rect.centerx + probe_offset, self.rect.bottom - 10, 10, 10)
            if any(probe_rect.colliderect(tile.rect) for tile in collision_group):
                self.velocity.y = self.jump_speed
        
        # Spawn Minion Logic
        if abs(dist_x) >= 256 and self.minion_cooldown == 0:
            self.minion_cooldown = 5
            m_pos = (self.rect.left + (32*(1 if dist_x>0 else -1)), self.rect.top)
            for _ in range(5): # Enemy spawn particles
                self.particle_group.add(Particle(m_pos, (255, 255, 255), 1)) 
            return Enemy(
                *m_pos, # Position of enemy
                width=16, # Width
                height=16, # Height
                max_hp=3, # Maximum HP
                always_chase=True # Always chase player
            )

    def state_musket(self, player, dt, collision_group):        
        self.velocity.x = 0

        if self.musket_hit_point and self.musket_warned:
            if player.rect.clipline(
                (self.rect.centerx, self.rect.centery),
                (self.musket_hit_point.x , self.musket_hit_point.y)
            ):
                player.die()
                self.bg_track.stop()
            self.state = "random"
            self.shoot_sfx.play()
            return
        
        if not self.musket_aimed:
            self.musket_hit_point = pg.Vector2(player.rect.center) # Musket 'hit point' will be player pos
            rel_vec = self.musket_hit_point - self.rect.center
            angle = rel_vec.as_polar()[1]
            
            # Musket Visuals
            if self.musket_hit_point.x < self.rect.centerx:
                self.musket_image_r = pg.transform.rotate(pg.transform.flip(self.musket_image, True, False), -angle + 180)
            else:
                self.musket_image_r = pg.transform.rotate(self.musket_image, -angle)
                
            self.musket_rect_r = self.musket_image_r.get_rect(center=self.rect.center)

    def state_bomb(self, player, dt, collision_group):
        self.velocity.x = 0
        if self.bomb_cooldown <= 0:
            if self.bombs_thrown >= 5:
                self.bombs_thrown = 0
                self.state = "random" 
                return
            self.bomb_cooldown = 1
            start = (self.rect.left, self.rect.top - 10)
            vel = utils.solve_velocity(*start, *player.rect.topleft, 0.8, 0.95)
            self.bomb_group.add(Bomb(*start, 8, 8, *vel))
            self.bombs_thrown += 1

    def state_hit(self, player, dt, collision_group):
        self.velocity.x = 0
        self.hit_time += dt
        if self.hit_time >= self.stun_time:
            self.hit_time = 0
            self.state = "random"

    def apply_physics(self, dt, collision_group):
        self.pos.x += self.velocity.x * (dt * 60)
        self.rect.x = round(self.pos.x)
        self.handle_collisions(collision_group, 'horizontal')

        self.on_ground = False
        self.velocity.y += self.gravity
        self.pos.y += self.velocity.y * (dt * 60)
        self.rect.y = round(self.pos.y)
        self.handle_collisions(collision_group, 'vertical')

    def animate(self, dt):
        if self.state == "hit": state_key = "hit"
        else:
            state_key = 'run' if abs(self.velocity.x) > 0.1 else 'idle'
            
        self.frame_index = (self.frame_index + self.animation_speed * (dt * 60)) % len(self.animations[state_key])
        self.image = pg.transform.flip(self.animations[state_key][int(self.frame_index)], self.flip, False)

    def update_child_sprites(self, player, dt, collision_group):
        # Update Bombs & Explosions
        for b in self.bomb_group: 
            e = b.update(dt, collision_group)
            if e: self.explosion_group.add(e)
        
        self.explosion_group.update(dt)

        # Update Particles
        self.particle_group.update(dt)

        # Check Explosion Damage to Player
        if player.rect.collidelist([e.rect for e in self.explosion_group]) != -1: 
            player.die()
            self.bg_track.stop()

    def handle_damage(self, player, collision_group):
        # Only take damage if not in the 'hit' state
        if self.state == 'hit': return

        for swish in player.swish_group:
            if swish.rect.colliderect(self.rect):
                # Spawn hit particles
                for _ in range(5):
                    self.particle_group.add(Particle(self.rect.center, (255, 255, 255), 0.25)) 

                # Play sound effect
                self.hit_sfx.play()
                
                # If in the bomb or musket state, do not take damage but do show partices and play SFX (done earlier).
                if self.state in ['musket', 'bomb']: return

                # Reduce Health
                self.hp -= 1
                
                # Trigger State Change
                self.state = 'hit'
                self.hit_time = 0 # Reset timer
                
                # Knockback
                if player.rect.centerx != self.rect.centerx:
                    knock_dir = 1 if self.rect.centerx > player.rect.centerx else -1
                    self.pos.x += knock_dir * 20
                    self.rect.x = round(self.pos.x)
                    self.handle_collisions(collision_group, 'horizontal')
                
                # Stop Checking Other Swishes Once Hit
                break 

    def update(self, player, dt, collision_group):
        # Update Cooldowns and Timers
        self.bomb_cooldown = max(0, self.bomb_cooldown - dt)
        self.minion_cooldown = max(0, self.minion_cooldown - dt)
        if self.state == "musket":
            if self.musket_aimed:
                self.musket_warn_timer = max(0, self.musket_warn_timer - dt)
            else:
                self.musket_aim_timer = max(0, self.musket_aim_timer - dt)
            self.musket_aimed = self.musket_aim_timer == 0
            self.musket_warned = self.musket_warn_timer == 0

        # Call Method for Current State
        state_return_value = self.states[self.state](player, dt, collision_group)

        # Physics & Collisions
        self.apply_physics(dt, collision_group)

        # Animate
        self.flip = player.rect.x < self.pos.x
        self.animate(dt)

        # Update Child Spries
        self.update_child_sprites(player, dt, collision_group)

        # Handle Damage
        self.handle_damage(player, collision_group)
        if self.hp <= 0: 
            self.kill()
            return
        
        return state_return_value

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))
        for b in self.bomb_group: b.draw(screen, camera)
        for e in self.explosion_group: e.draw(screen, camera)

        for p in self.particle_group: p.draw(screen, camera)

        if self.state == "musket":
            screen.blit(
                self.musket_image_r, 
                (self.musket_rect_r.x - camera[0], self.musket_rect_r.y - camera[1]) # Account for camera
            )
            if self.musket_hit_point:
                timer = self.musket_aim_timer if not self.musket_aimed else self.musket_warn_timer
                time = self.musket_aim_time if not self.musket_aimed else self.musket_warn_time
                color_value = timer * (255 / time * 5) % 255
                
                utils.draw_low_res_line(
                    screen,
                    (
                        (255, color_value, color_value) 
                        if not self.musket_aimed else 
                        (255, 255, color_value)
                    ),
                    (self.rect.centerx - camera[0], self.rect.centery - camera[1]), # From boss
                    (self.musket_hit_point.x - camera[0], self.musket_hit_point.y - camera[1]), # To hit point
                )

        health_bar_bg = pg.Surface((self.max_hp*10, 5))
        health_bar_bg.fill((0,0,0))
        health_bar_fg = pg.Surface((self.hp*10, 5))
        health_bar_fg.fill((255,0,0))
        screen.blit(
            health_bar_bg, 
            health_bar_bg.get_rect(
                center=pg.Vector2(self.rect.center) + (0,-20) - camera
            )
        )
        screen.blit(
            health_bar_fg, 
            health_bar_fg.get_rect(
                center=pg.Vector2(self.rect.center) + (-(self.max_hp-self.hp)*5,-20) - camera
            )
        )

    def kill(self):
        self.bg_track.stop()
        super().kill()