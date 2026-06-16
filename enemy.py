# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import utils

class Enemy(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, speed=2, max_hp=1, always_chase=False):
        super().__init__()

        # Visuals
        self.animations = {
            'idle': utils.load_animation('./assets/enemy/idle.png', width, height),
            'run':  utils.load_animation('./assets/enemy/run.png', width, height),
            'hit':  utils.load_animation('./assets/enemy/hit.png', width, height)
        }
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))

        # HP and Hit Time
        self.max_hp = max_hp
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

        # Enemy AI Parameters
        self.state = "patrol"
        self.detection_range = 200
        self.spawn_x = x
        self.patrol_range = 150
        self.patrol_direction = 1
        self.always_chase = always_chase

        # SFX
        self.hit_sfx = pg.mixer.Sound('./assets/sfx/hit.ogg')

    def can_see_player(self, player, collision_group):
        """Checks if a wall is blocking the view, filtered by distance."""
        start = self.rect.center
        end = player.rect.center
        
        # Use squared distance to avoid math.sqrt()
        max_dist_sq = self.detection_range ** 2
        
        for tile in collision_group: # Check if player is in the maximun distance and in the line of sight
            dist_sq = (tile.rect.centerx - start[0])**2 + (tile.rect.centery - start[1])**2
            if dist_sq < max_dist_sq:
                if tile.rect.clipline(start, end):
                    return False
        return True

    def handle_collisions(self, collision_group, axis):
        for tile in collision_group:
            if self.rect.colliderect(tile.rect):
                if axis == 'horizontal':
                    if self.velocity.x > 0: self.rect.right = tile.rect.left
                    if self.velocity.x < 0: self.rect.left = tile.rect.right
                    self.pos.x = self.rect.x
                    if self.state == "patrol": self.patrol_direction *= -1
                elif axis == 'vertical':
                    if self.velocity.y > 0:
                        self.rect.bottom = tile.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                    elif self.velocity.y < 0:
                        self.rect.top = tile.rect.bottom
                        self.velocity.y = 0
                    self.pos.y = self.rect.y

    def update(self, player, dt, collision_group):
        if self.state == "hit":
            self.hit_time += dt
            if self.hit_time >= self.stun_time:
                self.hit_time = 0
                self.state = "chase"

            # Play hit animation
            state_key = 'hit'
            self.frame_index = (self.frame_index + self.animation_speed * (dt * 60)) % len(self.animations[state_key])
            self.image = pg.transform.flip(self.animations[state_key][int(self.frame_index)], self.flip, False)

            return
        
        # Player Detection
        dist_x = player.rect.centerx - self.rect.centerx
        dist_y = player.rect.centery - self.rect.centery
        distance_sq = dist_x**2 + dist_y**2

        # Chase only if in range AND line of sight is clear
        if self.always_chase or (distance_sq < self.detection_range**2 and self.can_see_player(player, collision_group)):
            self.state = "chase"
            self.velocity.x = self.speed if dist_x > 0 else -self.speed
            self.flip = dist_x < 0
        else:
            # Patrol Logic
            self.state = "patrol"
            if self.rect.x > self.spawn_x + self.patrol_range: self.patrol_direction = -1
            elif self.rect.x < self.spawn_x - self.patrol_range: self.patrol_direction = 1
            self.velocity.x = (self.speed * 0.5) * self.patrol_direction
            self.flip = self.patrol_direction == -1

        # Jump Logic
        if self.on_ground:
            probe_offset = 25 if self.velocity.x > 0 else -25
            probe_rect = pg.Rect(self.rect.centerx + probe_offset, self.rect.bottom - 10, 10, 10)
            for tile in collision_group:
                if probe_rect.colliderect(tile.rect):
                    self.velocity.y = self.jump_speed
                    break

        # Physics
        self.pos.x += self.velocity.x * (dt * 60)
        self.rect.x = round(self.pos.x)
        self.handle_collisions(collision_group, 'horizontal')

        self.on_ground = False
        self.velocity.y += self.gravity
        self.pos.y += self.velocity.y * (dt * 60)
        self.rect.y = round(self.pos.y)
        self.handle_collisions(collision_group, 'vertical')

        # Animate
        state_key = 'run' if abs(self.velocity.x) > 0.1 else 'idle'
        self.frame_index = (self.frame_index + self.animation_speed * (dt * 60)) % len(self.animations[state_key])
        self.image = pg.transform.flip(self.animations[state_key][int(self.frame_index)], self.flip, False)

        # Damage Health if Touching Swish
        if self.state != 'hit':
            for swish in player.swish_group:
                if swish.rect.colliderect(self.rect):
                    self.hp -= 1
                    self.hit_sfx.play()
                    self.state = 'hit'
                    if player.rect.centerx != self.rect.centerx:
                        knock_dir = 1 if self.rect.centerx > player.rect.centerx else -1
                        self.pos.x += knock_dir * 20  # Pop them back 20 pixels
                        self.rect.x = round(self.pos.x)
                        self.handle_collisions(collision_group, 'horizontal')
                    # self.rect.center = (self.rect.centerx, self.rect.centery + v.y*2)
                    # self.handle_collisions(collision_group, 'vertical')

        if self.hp <= 0:
            player.kills += 1
            self.kill()

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))