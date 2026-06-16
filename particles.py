# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import random

class Particle(pg.sprite.Sprite):
    def __init__(self, pos, color, lifetime):
        super().__init__()
        self.pos = pg.math.Vector2(pos)
        # Random burst direction
        self.vel = pg.math.Vector2(random.uniform(-3, 3), random.uniform(-5, -1))
        self.size = random.randint(3, 6)
        self.color = color
        self.lifetime = lifetime # This is in seconds

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.vel * (dt * 60)
        self.vel.y += 0.2  # Gravity
        self.size = max(0, self.size - 0.1) # Shrink
        if self.lifetime <= 0 or self.size <= 0:
            self.kill()

    def draw(self, screen, camera):
        pg.draw.circle(screen, self.color, (self.pos.x - camera[0], self.pos.y - camera[1]), int(self.size))