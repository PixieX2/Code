import pygame
import numpy as np
from noise import pnoise1
import os
import sys

# --- Lang system compatible with PyInstaller onefile ---
class LangFile:
    def __init__(self, path):
        self.strings = {}
        self.base_path = getattr(
            sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
        )
        full_path = os.path.join(self.base_path, path)
        with open(full_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = map(str.strip, line.split("=", 1))
                    self.strings[k] = v

    def get(self, key):
        return self.strings.get(key, key)


lang = LangFile("langs/en-US.lang")

# --- Game setup ---
SCREEN = (1200, 800)  # bigger window
CELL_SIZE = 40
GRID_HEIGHT = SCREEN[1] // CELL_SIZE

pygame.init()
screen = pygame.display.set_mode(SCREEN)
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# --- Blocks ---
block_colors = {
    1: (0, 255, 0),       # Grass
    2: (128, 128, 128),   # Stone
    3: (139, 69, 19)      # Dirt
}

block_names = {
    1: lang.get("grass"),
    2: lang.get("stone"),
    3: lang.get("dirt")
}

inventory_slots = [
    1,  # Grass
    2,  # Stone
    3   # Dirt
]

selected_slot = 0


# --- Player ---
player_x, player_y = 0.0, 0.0
player_w, player_h = CELL_SIZE, CELL_SIZE
player_vel_x, player_vel_y = 0.0, 0.0
gravity = 0.5
jump_power = -10
on_ground = False
speed = 200  # pixels/sec

# --- Infinite world storage ---
world = {}  # world[x][y] = block_id
seed = 21684


def generate_column(x):
    height = int(pnoise1((x + seed) / 10, repeat=99999) * 5 + 5)
    col = {}
    for y in range(height + 1):
        if y == height:
            col[y] = 1  # grass
        elif y > height - 3:
            col[y] = 3  # dirt
        else:
            col[y] = 2  # stone
    return col


def get_block(x, y):
    if x not in world:
        world[x] = generate_column(x)
    return world[x].get(y, 0)


def set_block(x, y, block):
    if x not in world:
        world[x] = generate_column(x)
    world[x][y] = block


# --- Main loop ---
running = True
while running:
    dt = clock.tick(60) / 1000  # seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            gx = (
                int(player_x // CELL_SIZE)
                - SCREEN[0] // (2 * CELL_SIZE)
                + mx // CELL_SIZE
            )
            gy = GRID_HEIGHT - 1 - (my // CELL_SIZE)
            if event.button == 1:
                set_block(gx, gy, 0)
            elif event.button == 3:
                set_block(gx, gy, inventory_slots[selected_slot])
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                selected_slot = 0
            if event.key == pygame.K_2:
                selected_slot = 1
            if event.key == pygame.K_3:
                selected_slot = 2

    # --- Input ---
    keys = pygame.key.get_pressed()
    player_vel_x = 0.0
    if keys[pygame.K_a]:
        player_vel_x = -speed * dt
    if keys[pygame.K_d]:
        player_vel_x = speed * dt
    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = jump_power
        on_ground = False

    # --- Physics ---
    player_vel_y += gravity

    # Horizontal collision
    new_x = player_x + player_vel_x
    player_rect = pygame.Rect(new_x, player_y, player_w, player_h)
    for x in range(int(new_x // CELL_SIZE) - 1, int(new_x // CELL_SIZE) + 2):
        col = world.get(x, generate_column(x))
        for y in col:
            if col[y] == 0:
                continue
            block_rect = pygame.Rect(
                x * CELL_SIZE, SCREEN[1] - (y + 1) * CELL_SIZE, CELL_SIZE, CELL_SIZE
            )
            if player_rect.colliderect(block_rect):
                if player_vel_x > 0:
                    new_x = block_rect.left - player_w
                elif player_vel_x < 0:
                    new_x = block_rect.right
                player_rect.x = new_x
    player_x = new_x

    # Vertical collision
    new_y = player_y + player_vel_y
    player_rect.y = new_y
    on_ground = False
    for x in range(int(player_x // CELL_SIZE) - 1, int(player_x // CELL_SIZE) + 2):
        col = world.get(x, generate_column(x))
        for y in col:
            if col[y] == 0:
                continue
            block_rect = pygame.Rect(
                x * CELL_SIZE, SCREEN[1] - (y + 1) * CELL_SIZE, CELL_SIZE, CELL_SIZE
            )
            if player_rect.colliderect(block_rect):
                if player_vel_y > 0:
                    new_y = block_rect.top - player_h
                    player_vel_y = 0
                    on_ground = True
                elif player_vel_y < 0:
                    new_y = block_rect.bottom
                    player_vel_y = 0
                player_rect.y = new_y
    player_y = new_y

    # --- Draw ---
    screen.fill((135, 206, 235))

    # Draw visible columns
    cam_offset = player_x - SCREEN[0] // 2
    left_col = int(cam_offset // CELL_SIZE) - GRID_HEIGHT
    right_col = int(cam_offset // CELL_SIZE) + GRID_HEIGHT
    for x in range(left_col, right_col + 1):
        col = world.get(x, generate_column(x))
        for y, block in col.items():
            if block == 0:
                continue  # skip air
            rect = pygame.Rect(
                (x * CELL_SIZE - cam_offset),
                SCREEN[1] - (y + 1) * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(screen, block_colors[block], rect)

    # Draw player
    player_draw_rect = pygame.Rect(SCREEN[0] // 2, player_rect.y, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, (255, 255, 0), player_draw_rect)

    # --- UI ---
    text = font.render(
        f"Selected: {block_names[inventory_slots[selected_slot]]}", True, (0, 0, 0)
    )
    screen.blit(text, (10, 10))
    coord_text = font.render(f"Player X: {int(player_x//CELL_SIZE)}", True, (0, 0, 0))
    screen.blit(coord_text, (10, 30))
    controls_text = font.render(
        "Controls: A/D=Move SPACE=Jump 1-3=Select LMB/RMB=Break/Place", True, (0, 0, 0)
    )
    screen.blit(controls_text, (10, 50))

    pygame.display.flip()
