# Copyright (c) 2026 Shaurya Sharma
# SPDX-License-Identifier: MIT

# Import and initialize pygame-ce
import pygame as pg
pg.init()

# Other imports
from player import Player
from level import setup_level, draw_level_text, SCROLL_LEVELS, FINAL_LEVEL
import utils
from ui import draw_stat_indicator, Toggle
from enemy import Enemy
import pygame_textinput
import sys

# Colors + screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLUE, RED, GREEN, WHITE, BLACK = (135, 206, 235), (200, 0, 0), (34, 139, 34), (255, 255, 255), (0, 0, 0)

# Key pygame variables + window title
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pg.time.Clock()
pg.display.set_caption("Scout of Liberty")

# Font
font_64 = pg.font.Font('./assets/ui/PixelifySans.ttf', 64)
font_32 = pg.font.Font('./assets/ui/PixelifySans.ttf', 32)
font_16 = pg.font.Font('./assets/ui/PixelifySans.ttf', 16)

# Icons
icons = {
    'coin-icon-32': None,
    'kill-icon-32': None,
    'clock-icon-32': None,
    'death-icon-32': None,
    'skip-icon-32': None,
}
for k, v in icons.items(): icons[k] = pg.image.load(f'./assets/ui/{k}.png').convert_alpha()

def reset_level():
    global tiles, collision_group, enemy_group, danger_group, finish_point, level_info, player, scroll_x, boss
    tiles, collision_group, enemy_group, danger_group, finish_point, boss, level_info = setup_level(level)
    scroll_x = 0
    player = Player(0, 608)
    
# Game state and level data
state = "MENU"
level = 0 # Current level (0 is the tutorial level)
reset_level()
camera = [(player.rect.x - SCREEN_WIDTH/2), (player.rect.y - SCREEN_HEIGHT/2)] # Start on player
finished_game = False
player_stats = {}
time_spent_on_current_level = 0
deaths_on_current_level = 0
level_skipped = False
level_stats = {l: setup_level(l, stats=True) for l in range(1,FINAL_LEVEL+1)}
total_spawned_coins = None
total_spawned_enemies = None

# Stats menu
stats_menu_nav_dir = 0 # Navigation direction for stats menu
stats_menu_page_number = 1 # Page number for stats menu
toggle_a = Toggle(250, 525, 32, 16, "Collected vs Remaining", font_16)
toggle_b = Toggle(550, 525, 32, 16, "Efficiency Per Second", font_16)

# Fade in/out variables
fade_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
fade_surface.fill(BLACK)
fade_alpha = 0
fade_speed = 1360
since_fade = 0

# Name Input
name_input_manager = pygame_textinput.TextInputManager(validator = lambda input: len(input) <= 7)
name_input = pygame_textinput.TextInputVisualizer(manager=name_input_manager, font_object=font_32)
name_input.cursor_width = 4
name_input.cursor_blink_interval = 400 # blinking interval in ms
name_input.antialias = False
name_input.font_color = BLACK
name = None

# Instructions screen text
INSTRUCTIONS_TEXT = [
    # Preamble/Introduction
    "Scout of Liberty is a 2D platformer game made in Python. It is set in the 1770s",
    "during the American Revolution. The player is a fictional member of the Sons of Liberty",
    "who acts as a scout for the group. The game features two engaging levels:",
    "",

    # Controls
    "Controls:",
    "WASD/arrow keys to move.",
    "Space bar can also be used to jump.",
    "Double jump by jumping in the air.",
    "Left click to attack.",
    "",

    # Level 1 Info
    "Level 1: The Boston Tea Party - Inspired by the Boston Tea Party, this level allows the player",
    "to experience open and closed combat while attempting to make it to the other side of the ship.",
    "",

    # Level 2 Info
    "Level 2: The Midnight Ride - Inspired by Paul Revere's Midnight Ride, this level tasks the player to",
    "act quickly through the use of autoscrolling. The level features several possible detours for",
    "coins, engaging players by forcing them to chose between the risk of losing time and reward of coins.",
    "",

    # Level 3 & 4 Info
    "Level 3 & 4: The Battle of Yorktown (Parts 1 and 2) - Inspired by the Battle of Yorktown, these levels",
    "task the player to infiltrate the British-controlled Yorktown. The player must navigate through",
    "hordes of troops. This leads up to a final boss battle in Level 4 where the player fights a British general."
]

while True:
    dt = clock.tick(60) / 1000.0 # Delta time
    events = pg.event.get()
    mouse_pos = pg.mouse.get_pos()
    keys = pg.key.get_pressed()

    # Event loop
    for event in events:
        if event.type == pg.QUIT: 
            pg.quit()
            sys.exit()

        if event.type == pg.MOUSEBUTTONDOWN:
            if state == "MENU":
                if start_btn.collidepoint(mouse_pos): state = "INSTRUCTIONS"
                if credits_btn.collidepoint(mouse_pos): state = "CREDITS"
            elif state == "CREDITS":
                state = "MENU" # Click anywhere to close credits
            elif state == "INSTRUCTIONS":
                if next_btn.collidepoint(mouse_pos): state = "NAME_ENTER"
            elif state == "NAME_ENTER":
                if len(name_input.value) >= 1:
                    if next_btn.collidepoint(mouse_pos): 
                        name = name_input.value
                        state = "PLAYING"
                        reset_level()
                        camera = [(player.rect.x - SCREEN_WIDTH/2), (player.rect.y - SCREEN_HEIGHT/2)] # Start on player
            elif state == "PLAYING":
                if skip_btn.collidepoint(mouse_pos):
                    state = "FADING_OUT"
                    level_skipped = True
                elif since_fade >= 0.1: # Wait for a tenth of a second before processessing player input 
                    player.attack()
                
            elif state == "END":
                if stats_menu_page_number == 1 or not player_stats[stats_menu_current_level]['skipped']:
                    # Handle Toggle B first
                    if toggle_b.handle_event(event):
                        if toggle_b.is_on:
                            toggle_a.is_on = False  # Lock it to "Collected/Killed" side
                            toggle_a.is_locked = True
                        else:
                            toggle_a.is_locked = False

                    # Handle Toggle A
                    toggle_a.handle_event(event)

        if event.type == pg.KEYDOWN:
            if state == "PLAYING":
                if event.key in [pg.K_SPACE, pg.K_UP, pg.K_w] and since_fade >= 0.1: # Wait for a tenth of a second before processessing player input
                    player.jump()
            if state == "END":
                # If we have clicked left or right, get the direction we have pressed and save it to the variable
                if event.key in [pg.K_LEFT, pg.K_RIGHT]:
                    stats_menu_nav_dir = 1 if event.key == pg.K_RIGHT else -1
                else:
                    stats_menu_nav_dir = 0
        
    if state == "PLAYING":
        since_fade += dt
        time_spent_on_current_level += dt
        if player.update(
            dt, 
            keys if since_fade >= 0.1 else utils.NoKeysPressed(), # Wait for a tenth of a second before processessing player input
            collision_group, 
            danger_group,
            level_info, 
            enemy_group,
            boss
        ) == "dead":
            state = "FADING_OUT"
            deaths_on_current_level += 1
            continue
        enemy_group.update(player, dt, collision_group)
        if boss is not None and boss.hp > 0:
            boss_update_value = boss.update(player, dt, collision_group)
            if type(boss_update_value) == Enemy:
                enemy_group.add(boss_update_value)
                level_stats[4]['enemies'] += 1

        if player.rect.colliderect(finish_point.rect): state = 'FADING_OUT' # Begin fading out if player collided with finish point
        if boss:
            if boss.hp > 0: # If boss is alive
                player.rect.centerx = min(player.rect.centerx, 1270)
        if level in SCROLL_LEVELS and since_fade >= 3: # If the level loaded 3 seconds ago and the player is on a scroll level, begin scrolling.
            scroll_x += 90 * dt
            if player.rect.x < scroll_x:
                player.die()

        # Camera
        camera[0] += (player.rect.x - camera[0] - SCREEN_WIDTH/2) / 10
        camera[1] += (player.rect.y - camera[1] - SCREEN_HEIGHT/2) / 10
        camera[0] = max(min(camera[0], level_info.tilewidth*level_info.width-SCREEN_WIDTH), scroll_x)
        camera[1] = min(camera[1], 40)

    elif state == "FADING_OUT":
        fade_alpha += fade_speed * dt
        since_fade = 0
        if fade_alpha >= 255:
            fade_alpha = 255
            if not player.is_dead: # If the player didn't die, they must have finished or skipped the level.
                if level_skipped:
                    player_stats[level] = {
                        'coins': 0,
                        'kills': 0,
                        'time': 0,
                        'deaths': 0,
                        'skipped': level_skipped
                    }
                else:
                    player_stats[level] = {
                        'coins': player.coins,
                        'kills': player.kills,
                        'time': time_spent_on_current_level,
                        'deaths': deaths_on_current_level,
                        'skipped': level_skipped
                    }
                time_spent_on_current_level = 0
                deaths_on_current_level = 0
                level_skipped = False
                if level < FINAL_LEVEL: level += 1
                else: 
                    finished_game = True
                    # Sum up the all stats (excluding the tutorial level)
                    total_coins = sum([player_stats[l]['coins'] for l in player_stats.keys() if l > 0])
                    total_kills = sum([player_stats[l]['kills'] for l in player_stats.keys() if l > 0])
                    total_deaths = sum([player_stats[l]['deaths'] for l in player_stats.keys() if l > 0])
                    total_time_spent = sum([player_stats[l]['time'] for l in player_stats.keys() if l > 0])
                    total_skipped = sum([player_stats[l]['skipped'] for l in player_stats.keys() if l > 0]) # Adding booleans is allowed in Python
                    total_spawned_coins = sum([level_stats[l]['coins'] for l in level_stats.keys() if l > 0])
                    total_spawned_enemies = sum([level_stats[l]['enemies'] for l in level_stats.keys() if l > 0])
                    # Score = 3 * kills + coins collected
                    score = 3 * total_kills + total_coins 
            
            if not finished_game: reset_level() # Load level while screen is black if we haven't finished the game
            state = "FADING_IN"

    elif state == "FADING_IN":
        fade_alpha -= fade_speed * dt
        if fade_alpha <= 0:
            fade_alpha = 0
            if finished_game:
                state = "END"
            else:
                state = "PLAYING"

    elif state == "NAME_ENTER":
        name_input.update(events)

    # Render
    screen.fill(BLUE)
    if state == "MENU":
        utils.draw_text("Scout of Liberty", 400, 150, font_64, screen, BLACK)
        start_btn = pg.draw.rect(screen, GREEN, (300, 250, 200, 50))
        credits_btn = pg.draw.rect(screen, RED, (300, 320, 200, 50))
        utils.draw_text("START", 400, 275, font_32, screen, BLACK)
        utils.draw_text("CREDITS", 400, 345, font_32, screen, BLACK)

        # Draw images of player and redcoat
        screen.blit(
            pg.transform.rotate(
                pg.transform.scale(player.anim['idle'][0], 
                    (256,256)), 
                    -10), 
                (-75,350)
            )
        screen.blit(
            pg.transform.rotate(
                pg.transform.scale(
                    pg.transform.flip(utils.load_animation('./assets/enemy/idle.png', 16, 16)[0], True, False), 
                        (256,256)), 
                        10), 
                    (SCREEN_WIDTH-225,350)
            )

    elif state == "CREDITS":
        pg.draw.rect(screen, WHITE, (137.5, 150, 525, 300)) # Popup box
        utils.draw_text("Created by Shaurya Sharma", 400, 200, font_32, screen, BLACK)
        utils.draw_text("Full credits and attribution", 400, 250, font_32, screen, BLACK)
        utils.draw_text("are in the DISCLOSURE.md file", 400, 300, font_32, screen, BLACK)
        utils.draw_text("Click to close", 400, 400, font_32, screen, BLACK)

    elif state == "INSTRUCTIONS":
        # Header and text
        utils.draw_text("Instructions", 400, 25, font_32, screen, BLACK)
        for i in range(len(INSTRUCTIONS_TEXT)): utils.draw_text(INSTRUCTIONS_TEXT[i], 400, 50+i*25, font_16, screen, BLACK)

        # Next button
        next_btn = pg.draw.rect(screen, GREEN, (350, 540, 100, 50))
        utils.draw_text("NEXT", 400, 565, font_32, screen, BLACK)

    elif state in ["PLAYING", "FADING_OUT", "FADING_IN"]:
        tiles.update(screen, camera, dt, player) # Draw and animate tiles. For coins, this checks if the player has collected them.
        draw_level_text(level, font_32, font_16, screen, camera) # Draw any level text
        player.draw(screen, camera) # Draw player and swishes
        for e in enemy_group: e.draw(screen, camera) # Draw enemies
        if boss and boss.hp > 0: # Draw boss
            boss.draw(screen, camera)

        # Skip button
        if state == "PLAYING":
            skip_btn = pg.draw.rect(screen, GREEN, (SCREEN_WIDTH - 325, 20, 125, 50))
            screen.blit(icons["skip-icon-32"], (SCREEN_WIDTH - 320, 30))
            utils.draw_text("SKIP", SCREEN_WIDTH - 250, 45, font_32, screen, BLACK)

        # Draw coin indicator
        pg.draw.rect(screen, (40, 40, 40), (SCREEN_WIDTH - 150, 20, 100, 40), border_radius=10) # Background rectangle
        pg.draw.rect(screen, (180, 180, 180), (SCREEN_WIDTH - 150, 20, 100, 40), 2, border_radius=10) # Background rectangle
        screen.blit(icons["coin-icon-32"], (SCREEN_WIDTH - 142, 24)) # Coin icon
        utils.draw_text(f'  x {player.coins}', SCREEN_WIDTH - 100, 40, font_16, screen, WHITE) # Coin text

        if state in ["FADING_OUT", "FADING_IN"]: # If we are fading in or out, set the fade surface alpha and render it to the screen.
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))
            if pg.mixer.get_busy(): pg.mixer.stop() # Stop all sounds (if playing any)

    elif state == "END":
        # Congratulatory message + Header
        utils.draw_text(f"Congratulations {name}, you finished the game!", 400, 50, font_32, screen, BLACK)
        utils.draw_text("Statistical Overview", 400, 100, font_32, screen, BLACK)

        # Wrap around page navigation
        stats_menu_page_number += stats_menu_nav_dir
        if stats_menu_page_number < 1: stats_menu_page_number = 5
        if stats_menu_page_number > 5: stats_menu_page_number = 1

        # Page display
        if stats_menu_page_number == 1:
            # Final score
            utils.draw_text(f"Final Score: {score}", 400, 175, font_64, screen, BLACK)

            stats_overview_list = [
                ['clock-icon-32', f"{total_time_spent:.1f}s"],
                ['death-icon-32', f"{total_deaths} death(s)"],
                ['coin-icon-32', f"{total_coins} coin(s) collected"],
                ['kill-icon-32', f"{total_kills} kill(s)"],
                ['skip-icon-32', f"{total_skipped} skipped level(s)"],
            ]

            if toggle_b.is_on:
                if total_time_spent == 0:
                    stats_overview_list[2][1] = f"-- coin(s) per second"
                    stats_overview_list[3][1] = f"-- kill(s) per second"
                else:
                    stats_overview_list[2][1] = f"{total_coins/total_time_spent:.2f} coin(s) per second"
                    stats_overview_list[3][1] = f"{total_kills/total_time_spent:.2f} kill(s) per second"
            else:
                if toggle_a.is_on:
                    stats_overview_list[2][1] = f"{total_spawned_coins-total_coins} coin(s) left"
                    stats_overview_list[3][1] = f"{total_spawned_enemies-total_kills} enemy(ies) spared"
                else:
                    stats_overview_list[2][1] = f"{total_coins} coin(s) collected"
                    stats_overview_list[3][1] = f"{total_kills} kill(s)"

            for i in range(len(stats_overview_list)): 
                utils.draw_text(stats_overview_list[i][1], 400, 250+i*50, font_16, screen, BLACK)
                try: 
                    icon = icons[stats_overview_list[i][0]]
                    rect = icon.get_rect(center=(290,250+i*50))
                    screen.blit(icon, rect)
                except IndexError: pass # Ignore out-of-range indexes
            
            # Draw Toggles
            toggle_a.draw(screen)
            toggle_b.draw(screen)
        else:
            stats_menu_current_level = stats_menu_page_number-1
            utils.draw_text(f"Level {stats_menu_current_level}", 400, 175, font_64, screen, BLACK)
            if player_stats[stats_menu_current_level]["skipped"]: # If level skipped, just show that the level was skipped.
                utils.draw_text("LEVEL SKIPPED", 400, 300, font_32, screen, BLACK)
            else: # If level wasn't skipped, show the full level stats page

                # Total Time in Level
                draw_stat_indicator(
                    screen, 
                    (325,250), 
                    icons["clock-icon-32"],
                    f"{player_stats[stats_menu_current_level]['time']:.1f}s",
                    BLACK,
                    font_16
                )

                # Deaths During Level
                draw_stat_indicator(
                    screen, 
                    (475,250), 
                    icons["death-icon-32"],
                    f"{player_stats[stats_menu_current_level]['deaths']} death(s)",
                    BLACK,
                    font_16
                )

                # Separator
                pg.draw.line(
                    screen,
                    BLACK,
                    (100,300),
                    (700,300),
                    3
                )
                # Coin + Kill Indicator
                if toggle_b.is_on:
                    coin_indicator_text = f"{player_stats[stats_menu_current_level]['coins']/player_stats[stats_menu_current_level]['time']:.2f}/sec"
                    kill_indicator_text = f"{player_stats[stats_menu_current_level]['kills']/player_stats[stats_menu_current_level]['time']:.2f}/sec"
                else:
                    if toggle_a.is_on:
                        coin_indicator_text = f"{level_stats[stats_menu_current_level]['coins']-player_stats[stats_menu_current_level]['coins']} left"
                        kill_indicator_text = f"{level_stats[stats_menu_current_level]['enemies']-player_stats[stats_menu_current_level]['kills']} spared"
                    else:
                        coin_indicator_text = f"{player_stats[stats_menu_current_level]['coins']} collected"
                        kill_indicator_text = f"{player_stats[stats_menu_current_level]['kills']} killed"

                draw_stat_indicator(
                    screen, 
                    (325,350), 
                    icons["coin-icon-32"],
                    coin_indicator_text,
                    BLACK,
                    font_16
                )
                    
                draw_stat_indicator(
                    screen, 
                    (475,350), 
                    icons["kill-icon-32"],
                    kill_indicator_text,
                    BLACK,
                    font_16
                )

                # Drawing Toggles
                toggle_a.draw(screen)
                toggle_b.draw(screen)
        
        # Navigation
        utils.draw_text(f"{stats_menu_page_number}/5 - Left and right arrows to navigate", 400, 575, font_16, screen, BLACK)
        stats_menu_nav_dir = 0 # Reset nav dir each frame

    elif state == "NAME_ENTER":
        # Header
        utils.draw_text('Enter your name (7 character limit):', 400, 125, font_32, screen, BLACK)

        # Input Position and Width
        input_width = 150
        input_pos = (400-(input_width//2),200)

        # Rendering Input
        input_bg = pg.Surface((input_width, name_input.surface.get_rect().height))
        input_bg.fill(WHITE)
        screen.blit(input_bg, input_pos)
        screen.blit(name_input.surface, input_pos)

        # Next button
        next_btn = pg.draw.rect(screen, GREEN, (350, 540, 100, 50))
        utils.draw_text("NEXT", 400, 565, font_32, screen, BLACK)

    pg.display.update() # Update display