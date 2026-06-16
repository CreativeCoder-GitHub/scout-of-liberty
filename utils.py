# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import math

def draw_low_res_line(screen, color, start_pos, end_pos, res=256):
    sw, sh = screen.get_size()
    if sw > sh:
        lw, lh = res, int(res * (sh / sw))
    else:
        lw, lh = int(res * (sw / sh)), res
        
    low_res_surf = pg.Surface((max(1, lw), max(1, lh)), pg.SRCALPHA)
    scale = sw / lw
    x0, y0 = int(start_pos[0] / scale), int(start_pos[1] / scale)
    x1, y1 = int(end_pos[0] / scale), int(end_pos[1] / scale)
    pg.draw.line(low_res_surf, color, (x0, y0), (x1, y1), 1)
    final_surf = pg.transform.scale(low_res_surf, (sw, sh))
    screen.blit(final_surf, (0, 0))

def load_animation(filename, frame_width, frame_height):
    "Loads an animation from a single file with a given frame width and height"
    sheet = pg.image.load(filename).convert_alpha()
    frames = []
    frame_count = sheet.get_width() // frame_width
    for i in range(frame_count):
        rect = pg.Rect(i * frame_width, 0, frame_width, frame_height)
        frame = pg.transform.scale(sheet.subsurface(rect), (32, 32))
        frames.append(frame)
    return frames

def draw_text(text, x, y, font, screen, color, center=True):
    "Draws text to the screen."
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)

class NoKeysPressed:
    "Emulates a pygame ScancodeWrapper where no keys are pressed."
    def __getitem__(self, key): return False

class MoreKeysPressed:
    "Emulates a pygame ScancodeWrapper where given keys are always pressed."
    def __init__(self, wrapper: pg.key.ScancodeWrapper, pressed_keys: set): 
        self.wrapper = wrapper
        self.pressed_keys = pressed_keys
    def __getitem__(self, key): return self.wrapper[key] or key in self.pressed_keys

def solve_velocity(start_x, start_y, target_x, target_y, gravity, friction):
    dx = target_x - start_x
    dy = target_y - start_y
    
    low_power = 0
    high_power = 500
    best_vx, best_vy = 0, 0
    
    for _ in range(40):
        power = (low_power + high_power) / 2
        
        # Adjust the arc based on direction
        # We aim at the target, then offset UP (negative Y in Pygame)
        base_angle = math.atan2(dy, dx)
        if dx >= 0:
            angle = base_angle - (math.pi / 4) # Right-hand arc
        else:
            angle = base_angle + (math.pi / 4) # Left-hand arc
            
        vx = math.cos(angle) * power
        vy = math.sin(angle) * power
        
        # Simulation
        sim_x, sim_y = start_x, start_y
        sim_vx, sim_vy = vx, vy
        
        reached_target = False
        for _ in range(300): # 5 seconds of flight
            sim_vx *= friction
            sim_x += sim_vx
            
            sim_vy += gravity
            sim_y += sim_vy
            
            # Check horizontal crossing
            if (dx > 0 and sim_x >= target_x) or (dx < 0 and sim_x <= target_x):
                # If above or at target height
                if sim_y <= target_y:
                    reached_target = True
                break
            
            # Fail-safe
            if sim_y > target_y + 200 or abs(sim_vx) < 0.01:
                break
        
        if reached_target:
            high_power = power
            best_vx, best_vy = vx, vy
        else:
            low_power = power

    return best_vx, best_vy