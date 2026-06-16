# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

import pygame as pg
from pytmx.util_pygame import load_pygame
import utils
from enemy import Enemy
from boss import Boss

FINAL_LEVEL = 4 # Level 4 is the last level.

# Level 2 is the only scroller level. 
# However, if more were scroller levels were added, they would be added to this list.
SCROLL_LEVELS = [2]

def draw_level_text(level, font_32, font_16, screen, camera):
    "This function renders level-specific text."

    if level == 0:
        utils.draw_text('Tutorial Level', 250 - camera[0], 350 - camera[1], font_32, screen, (0,0,0))
        utils.draw_text('Collect coins', 500 - camera[0], 450 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('Double Jump', 600 - camera[0], 380 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('Enter the Finish Point to Beat the Level', 775 - camera[0], 176 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('Beat the Enemy', 750 - camera[0], 450 - camera[1], font_16, screen, (0,0,0))

    elif level == 1:
        utils.draw_text('Level 1: The Boston Tea Party', 300 - camera[0], 350 - camera[1], font_32, screen, (0,0,0))
        utils.draw_text('Get to the tea crates without being caught or falling in water.', 300 - camera[0], 400 - camera[1], font_16, screen, (0,0,0))

    elif level == 2:
        utils.draw_text('Level 2: The Midnight Ride', 300 - camera[0], 350 - camera[1], font_32, screen, (0,0,0))
        utils.draw_text('Reach the end of the path quickly without being caught.', 325 - camera[0], 400 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('THIS IS A SCROLLER LEVEL. If you go to the left of the screen, you die.', 325 - camera[0], 425 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('JUMP!!', 3392 - camera[0], 512 - camera[1], font_32, screen, (0,0,0))

    elif level == 3:
        utils.draw_text('Level 3: The Battle of Yorktown (Part 1)', 320 - camera[0], 350 - camera[1], font_32, screen, (0,0,0))
        utils.draw_text('Infiltrate a British-controlled Yorktown.', 320 - camera[0], 400 - camera[1], font_16, screen, (0,0,0))
    
    elif level == 4:
        utils.draw_text('Level 4: The Battle of Yorktown (Part 2)', 320 - camera[0], 350 - camera[1], font_32, screen, (0,0,0))
        utils.draw_text('Fight the British general!', 320 - camera[0], 400 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('The boss may only be attacked when it is chasing you. When it is', 320 - camera[0], 425 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('chasing you, it may also spawn enemies with 3 HP each. The boss may', 320 - camera[0], 450 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('use a musket. A red line means it is aiming, and a yellow line means', 320 - camera[0], 475 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('it will shoot soon. The boss can also throw bombs you must dodge.', 320 - camera[0], 500 - camera[1], font_16, screen, (0,0,0))

        utils.draw_text('Kill the boss before', 1200 - camera[0], 475 - camera[1], font_16, screen, (0,0,0))
        utils.draw_text('completing the level!', 1200 - camera[0], 500 - camera[1], font_16, screen, (0,0,0))


class Tile(pg.sprite.Sprite):
    "Simple class to render individual tiles. Coins count as tiles."
    def __init__(self, x, y, width, height, tile_id: int, hitbox: bool = True, frames=None):
        super().__init__()
        self.frames = frames # List of (image, duration) tuples
        self.frame_index = 0
        self.frame_timer = 0
        
        initial_img = frames[0][0] if frames else pg.Surface((width, height))
        self.image = pg.transform.scale(initial_img, (width, height))

        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = hitbox
        self.tile_id = tile_id

    def update(self, screen, camera, dt, player):
        """This function draws and animates the tile."""

        if self.frames:
            self.frame_timer += dt * 1000 # dt is in seconds but duration is in milliseconds
            # Check duration of current frame
            current_duration = self.frames[self.frame_index][1]
            if self.frame_timer >= current_duration:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                # Update image to next frame
                new_img = self.frames[self.frame_index][0]
                self.image = pg.transform.scale(new_img, (self.rect.width, self.rect.height))

        if self.is_coin:
            if self.rect.colliderect(player.rect): # Collect the coin
                player.collect_coin()
                self.kill()
                del self
                return

        screen.blit(self.image, (self.rect.x - camera[0], self.rect.y - camera[1]))

def setup_level(level_number, stats=False):
    # Load the TMX file + create groups and variables
    tmx_data = load_pygame(f'./assets/level/level{level_number}.tmx')
    if stats:
        level_stats = {'coins': 0, 'enemies': 0}
    else:
        tile_group = pg.sprite.Group()
        collision_group = pg.sprite.Group() 
        enemy_group = pg.sprite.Group()
        danger_group = pg.sprite.Group()
        boss = None

    # Loop through all layers (this allows for multiple layers, if needed)
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                props = tmx_data.get_tile_properties_by_gid(gid) or {}
                if not stats:
                    tile_image = tmx_data.get_tile_image_by_gid(gid) # Get the image of the tile

                    if tile_image:
                        frames = []
                        if 'frames' in props:
                            for frame in props['frames']:
                                # Get the actual image for this frame's GID
                                frame_image = tmx_data.get_tile_image_by_gid(frame.gid)
                                if frame_image:
                                    # Store (image, duration)
                                    frames.append((frame_image, frame.duration))

                    if props.get("is_enemy", False):
                        e = Enemy(x * tmx_data.tilewidth, y * tmx_data.tileheight, 
                            16, 16) # Enemy is 16x16 px
                        enemy_group.add(e)
                        continue

                    if props.get("is_boss", False):
                        boss = Boss(x * tmx_data.tilewidth, y * tmx_data.tileheight, 
                            16, 16) # Boss is 16x16 px
                        continue

                    tile_image = tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        t = Tile(
                            x * tmx_data.tilewidth, 
                            y * tmx_data.tileheight, 
                            tmx_data.tilewidth, 
                            tmx_data.tileheight,
                            gid,
                            props.get("hitbox", False),
                            frames=frames if frames else None
                        )
                        # If not animated, manually set the static image
                        if not frames:
                            t.image = pg.transform.scale(tile_image, (tmx_data.tilewidth, tmx_data.tileheight))
                        
                        t.is_finish = props.get("is_finish", False)
                        t.is_coin = props.get("is_coin", False)
                        
                        if props.get("hitbox", False): collision_group.add(t) # If the tile has a hitbox, add it to the collision group.
                        if props.get("danger", False): danger_group.add(t) # If the tile is marked as dangerous, add it to the danger group.
                        tile_group.add(t)
                else:                    
                    if tmx_data.get_tile_image_by_gid(gid):
                        props = tmx_data.get_tile_properties_by_gid(gid)
                    if props.get("is_enemy", False): level_stats['enemies'] += 1
                    if props.get("is_coin", False): level_stats['coins'] += 1
                    
    if stats:
        return level_stats
    else:
        finish_point = [t for t in tile_group if t.is_finish][0]
        return tile_group, collision_group, enemy_group, danger_group, finish_point, boss, tmx_data