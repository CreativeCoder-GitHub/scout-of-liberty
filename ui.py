# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
import utils

def draw_stat_indicator(screen, position, icon, text, text_color, font):
    screen.blit(icon, icon.get_rect(center=position))
    utils.draw_text(text, position[0], position[1]+25, font, screen, text_color)

class Toggle:
    def __init__(self, x, y, width, height, label, font, active_color=(0, 200, 0), inactive_color=(100,100,100), locked_color=(50,50,50)):
        self.rect = pg.Rect(x, y, width, height)
        self.label = label
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.locked_color = locked_color
        
        self.is_on = False
        self.is_locked = False
        self.font = font

    def draw(self, screen):
        # Dim the toggle if locked
        bg_color = self.active_color if self.is_on else self.inactive_color
        if self.is_locked:
            bg_color = self.locked_color
        
        # Draw background
        pg.draw.rect(screen, bg_color, self.rect, border_radius=self.rect.height//2)
        
        # Draw circle
        circle_x = self.rect.right - (self.rect.height // 2) if self.is_on else self.rect.left + (self.rect.height // 2)
        circle_color = (200, 200, 200) if self.is_locked else (255, 255, 255)
        pg.draw.circle(screen, circle_color, (circle_x, self.rect.centery), (self.rect.height // 2) - 4)
        
        # Draw label
        utils.draw_text(self.label, self.rect.x, self.rect.y - 10, self.font, screen, (0, 0, 0))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and not self.is_locked:
            if self.rect.collidepoint(event.pos):
                self.is_on = not self.is_on
                return True # Signal that a change happened
        return False
    
class VirtualJoystick:
    def __init__(self, x, y, radius=60, stick_radius=25):
        self.center = pg.Vector2(x, y)
        self.radius = radius
        self.stick_radius = stick_radius
        self.stick_pos = pg.Vector2(x, y)
        self.is_dragging = False
        self.active_keys = set()
        self.deadzone = radius * 0.3

    def is_hovered(self, pos):
        """Checks if a position is within the joystick base."""
        return self.center.distance_to(pos) < self.radius

    def handle_event(self, event):
        """Processes interaction and posts key events to the queue."""
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.is_hovered(event.pos):
                self.is_dragging = True
        
        elif event.type == pg.MOUSEBUTTONUP:
            if self.is_dragging:
                self.is_dragging = False
                self.stick_pos = pg.Vector2(self.center)
                self._update_keys(pg.Vector2(0, 0))

        if event.type == pg.MOUSEMOTION and self.is_dragging:
            offset = pg.Vector2(event.pos) - self.center
            if offset.length() > self.radius:
                offset.scale_to_length(self.radius)
            
            self.stick_pos = self.center + offset
            self._update_keys(offset)

    def _update_keys(self, offset):
        """Maps stick displacement to keys and posts events."""
        new_keys = set()
        
        if offset.length() > self.deadzone:
            # Vertical mapping
            if offset.y < -self.deadzone: 
                new_keys.add(pg.K_UP)
            elif offset.y > self.deadzone: 
                new_keys.add(pg.K_DOWN)
            
            # Horizontal mapping
            if offset.x < -self.deadzone: 
                new_keys.add(pg.K_LEFT)
            elif offset.x > self.deadzone: 
                new_keys.add(pg.K_RIGHT)

        # Release keys no longer active
        for key in (self.active_keys - new_keys):
            pg.event.post(pg.event.Event(pg.KEYUP, {'key': key}))
            
        # Press newly active keys
        for key in (new_keys - self.active_keys):
            pg.event.post(pg.event.Event(pg.KEYDOWN, {'key': key}))

        self.active_keys = new_keys

    def draw(self, surface):
        """Renders the joystick base and stick."""
        pg.draw.circle(surface, (100, 100, 100), self.center, self.radius, 2)
        stick_color = (255, 255, 255) if self.is_dragging else (180, 180, 180)
        pg.draw.circle(surface, stick_color, self.stick_pos, self.stick_radius)

class VirtualKeyboard:
    def __init__(self, x=50, y=300, font=None, key_w=45, key_h=45):
        self.key_w, self.key_h = key_w, key_h
        self.is_caps = False
        self.font = font
        self.keys_layout = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        self.buttons = []
        self._create_keyboard(x, y)

    def _create_keyboard(self, start_x, start_y):
        self.buttons = []
        #Letters + Backspace
        for col_idx, char in enumerate(self.keys_layout[0]):
            rect = pg.Rect(start_x + col_idx * (self.key_w + 5), start_y, self.key_w, self.key_h)
            self.buttons.append({'rect': rect, 'char': char, 'key': getattr(pg, f"K_{char.lower()}")})
        
        back_rect = pg.Rect(start_x + 10 * (self.key_w + 5), start_y, self.key_w * 1.8, self.key_h)
        self.buttons.append({'rect': back_rect, 'char': '', 'key': pg.K_BACKSPACE, 'label': 'BACK'})

        # Caps Lock + More Letters
        caps_w = self.key_w * 1.5
        caps_rect = pg.Rect(start_x, start_y + (self.key_h + 5), caps_w, self.key_h)
        self.buttons.append({'rect': caps_rect, 'char': '', 'key': pg.K_CAPSLOCK, 'label': 'CAPS'})

        for col_idx, char in enumerate(self.keys_layout[1]):
            rect = pg.Rect(start_x + caps_w + 5 + col_idx * (self.key_w + 5), start_y + (self.key_h + 5), self.key_w, self.key_h)
            self.buttons.append({'rect': rect, 'char': char, 'key': getattr(pg, f"K_{char.lower()}")})

        # Row 3: More Letters
        for col_idx, char in enumerate(self.keys_layout[2]):
            rect = pg.Rect(start_x + 30 + col_idx * (self.key_w + 5), start_y + 2 * (self.key_h + 5), self.key_w, self.key_h)
            self.buttons.append({'rect': rect, 'char': char, 'key': getattr(pg, f"K_{char.lower()}")})

        # Row 4: Space Bar
        space_w = self.key_w * 6
        space_rect = pg.Rect(start_x + (len(self.keys_layout[0]) * self.key_w)//4, start_y + 3 * (self.key_h + 5), space_w, self.key_h)
        self.buttons.append({'rect': space_rect, 'char': ' ', 'key': pg.K_SPACE, 'label': 'SPACE'})

    def _post_key(self, event_type, btn):
        if btn['key'] == pg.K_CAPSLOCK:
            if event_type == pg.KEYDOWN:
                self.is_caps = not self.is_caps
            return

        char_out = btn['char'] if self.is_caps else btn['char'].lower()
        event_data = {
            'key': btn['key'],
            'unicode': char_out if event_type == pg.KEYDOWN else '',
            'mod': pg.KMOD_CAPS if self.is_caps else pg.KMOD_NONE
        }
        pg.event.post(pg.event.Event(event_type, event_data))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                if btn['rect'].collidepoint(event.pos):
                    self._post_key(pg.KEYDOWN, btn)
        elif event.type == pg.MOUSEBUTTONUP:
            for btn in self.buttons:
                if btn['rect'].collidepoint(event.pos):
                    self._post_key(pg.KEYUP, btn)

    def draw(self, surface):
        for btn in self.buttons:
            color = (150, 255, 150) if btn['key'] == pg.K_CAPSLOCK and self.is_caps else (220, 220, 220)
            pg.draw.rect(surface, color, btn['rect'], border_radius=5)
            pg.draw.rect(surface, (40, 40, 40), btn['rect'], 2, border_radius=5)
            
            label = btn.get('label', btn['char'])
            if len(label) == 1:
                label = label if self.is_caps else label.lower()
                
            txt = self.font.render(label, True, (0, 0, 0))
            surface.blit(txt, txt.get_rect(center=btn['rect'].center))