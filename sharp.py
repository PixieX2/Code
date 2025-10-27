import pygame, sys, random, math, os
from math import sqrt

pygame.init()

# --- Lang system ---
class LangFile:
    def __init__(self, path):
        self.strings = {}
        self.base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(self.base_path, path)
        try:
            with open(full_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("!"): continue
                    if "=" in line:
                        k, v = map(str.strip, line.split("=", 1))
                        self.strings[k] = v
        except FileNotFoundError:
            pass
    def get(self, key):
        return self.strings.get(key, key)

lang = LangFile("langs/en-US.lang")

# --- Config ---
SCREEN = (1000, 700)
CELL_SIZE = 32
GRAVITY = 900.0   # pixels/sec²
JUMP_POWER = 450.0
SPEED = 220.0
LIGHT_RADIUS = 6
SEED = random.randint(0, 999999999999999)

screen = pygame.display.set_mode(SCREEN)
pygame.display.set_caption("MiniCraft")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 18)

# --- Blocks ---
block_colors = {
    1: (0, 255, 0),
    2: (139, 69, 19),
    3: (128, 128, 128),
    4: (237, 201, 175),
    5: (192, 192, 192),
    6: (0, 191, 255),
    7: (101, 67, 33),
    8: (34, 139, 34),
    9: (0,0,255),
    10: (255,0,0),
    11: (255,215,0),
    12: (255,250,250),
    13: (178,34,34),
}

block_names = {k: lang.get(v) if isinstance(v,str) else v for k,v in {
    1:"grass",2:"dirt",3:"stone",4:"sand",5:"iron",6:"d2o",7:"wood",8:"leaves",
    9:"water",10:"lava",11:"gold",12:"snow",13:"brick"
}.items()}

# --- Inventory ---
inventory = {k: 0 for k in block_colors.keys()}
selected_slot = 1

# --- World storage ---
world = {}
terrain_cache = {}
structures_generated = set()

def get_column(x):
    if x in world:
        return world[x]

    # --- Terrain generation ---
    if x in terrain_cache:
        h = terrain_cache[x]
    else:
        scale = 20.0
        seed_val = SEED
        h = int(5 + 10 * (
            0.5*(1 + math.sin((x+seed_val)/scale)) +
            0.3*(1 + math.sin((x+seed_val)/7.0))*0.5 +
            0.2*(1 + math.sin((x+seed_val)/3.0))*0.5
        ))
        terrain_cache[x] = h

    col = {}
    for y in range(h):
        if y == h-1: col[y] = 1
        elif y > h-4: col[y] = 2
        else:
            r = random.random()
            if r < 0.01: col[y] = 6
            elif r < 0.06: col[y] = 5
            else: col[y] = 3
    if random.random() < 0.02: col[h] = 4

    # --- Structures (only once per column) ---
    if x not in structures_generated:
        structures_generated.add(x)
        # House
        if random.random() < 0.03 and col.get(h-1,0)==1:
            width = random.randint(3,5)
            height = random.randint(3,4)
            for hx in range(x, x+width):
                col_hx = get_column(hx)
                for hy in range(h, h+height):
                    col_hx[hy] = 13
                col_hx[h+height] = 12
                world[hx] = col_hx
        # Tree
        if random.random() < 0.04 and col.get(h-1,0)==1:
            trunk_height = random.randint(3,5)
            for hx in range(x-1, x+2):
                col_hx = get_column(hx)
                for ty in range(h, h+trunk_height):
                    if hx == x: col_hx[ty] = 7
                # leaves
                for lx in range(-2,3):
                    for ly in range(0,3):
                        ty2 = h+trunk_height+ly
                        if abs(lx)+ly<3:
                            col_leaf = get_column(x+lx)
                            if ty2 not in col_leaf: col_leaf[ty2] = 8
                            world[x+lx] = col_leaf
                world[hx] = col_hx
        # Lake
        if random.random() < 0.02:
            lake_depth = random.randint(2,4)
            for lx in range(x-2, x+3):
                col_lx = get_column(lx)
                for ly in range(h-1, h-lake_depth-1, -1):
                    col_lx[ly] = 9
                world[lx] = col_lx

    world[x] = col
    return col

def get_block(cell_x, cell_y):
    return get_column(cell_x).get(cell_y, 0)

def set_block(cell_x, cell_y, bid):
    get_column(cell_x)[cell_y] = bid

# --- Player ---
def rect_collides(px, py):
    left, bottom = px, py
    right, top = px + CELL_SIZE, py + CELL_SIZE
    min_cx = int(left // CELL_SIZE)
    max_cx = int((right-1)//CELL_SIZE)
    min_cy = int(bottom // CELL_SIZE)
    max_cy = int((top-1)//CELL_SIZE)
    for cx in range(min_cx, max_cx+1):
        col = get_column(cx)
        for cy in range(min_cy, max_cy+1):
            if col.get(cy,0)!=0:
                return True
    return False

def move_player(px, py, dx, dy):
    steps = int(max(abs(dx), abs(dy),1))
    step_x = dx / steps
    step_y = dy / steps
    collided_vert = False
    for _ in range(steps):
        nx = px + step_x
        ny = py + step_y
        if not rect_collides(nx, ny):
            px, py = nx, ny
            continue
        if not rect_collides(px+step_x, py):
            px += step_x
            continue
        if not rect_collides(px, py+step_y):
            py += step_y
            continue
        if abs(step_y) > 0: collided_vert=True
        break
    return px, py, collided_vert

spawn_x = 0
col = get_column(spawn_x)
surface_y = max(col.keys()) if col else 0
player_x = spawn_x*CELL_SIZE
player_y = (surface_y+1)*CELL_SIZE
player_vel_x = 0.0
player_vel_y = 0.0
on_ground = True

# --- Main loop ---
running = True
while running:
    dt = clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type==pygame.QUIT: pygame.quit(); sys.exit()
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: running=False
            if pygame.K_1 <= event.key <= pygame.K_9: selected_slot = event.key - pygame.K_1 + 1
            if event.key==pygame.K_q: selected_slot=10
            if event.key==pygame.K_e: selected_slot=11
            if event.key==pygame.K_r: selected_slot=12
        elif event.type==pygame.MOUSEBUTTONDOWN:
            mx,my=pygame.mouse.get_pos()
            cam_offset = player_x - SCREEN[0]//2
            wx=int((mx+cam_offset)//CELL_SIZE)
            wy=int((SCREEN[1]-my)//CELL_SIZE)
            if event.button==1: set_block(wx,wy,0)
            elif event.button==3: set_block(wx,wy,selected_slot)

    # Input
    keys = pygame.key.get_pressed()
    player_vel_x = 0.0
    if keys[pygame.K_a]: player_vel_x=-SPEED
    if keys[pygame.K_d]: player_vel_x=SPEED
    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = JUMP_POWER
        on_ground=False

    # Gravity
    player_vel_y -= GRAVITY*dt
    dx = player_vel_x*dt
    dy = player_vel_y*dt
    player_x, player_y, collided_vert = move_player(player_x, player_y, dx, dy)

    # --- Ground detection fix ---
    if collided_vert and player_vel_y < 0:
        on_ground = True
        player_vel_y = 0.0
    else:
        # check if block directly below feet exists
        feet_y = (player_y - 1) // CELL_SIZE
        left_foot = int(player_x // CELL_SIZE)
        right_foot = int((player_x + CELL_SIZE - 1) // CELL_SIZE)
        grounded = False
        for foot_x in range(left_foot, right_foot + 1):
            if get_block(foot_x, int(feet_y)) != 0:
                grounded = True
                break
        on_ground = grounded

    # Sand falling
    px_cell=int(player_x//CELL_SIZE)
    for cx in range(px_cell-10,px_cell+11):
        col=get_column(cx)
        for y in sorted(list(col.keys())):
            if col.get(y,0)==4 and col.get(y-1,0)==0:
                col[y-1]=4
                col[y]=0

    # Draw
    screen.fill((135,206,235))
    cam_offset=player_x-SCREEN[0]//2
    left_col=int(cam_offset//CELL_SIZE)-3
    right_col=int(cam_offset//CELL_SIZE)+SCREEN[0]//CELL_SIZE+3
    for x in range(left_col,right_col+1):
        col=get_column(x)
        for y,bid in col.items():
            if bid==0: continue
            screen_x = x*CELL_SIZE - cam_offset
            screen_y = SCREEN[1] - ((y+1)*CELL_SIZE)
            rect = pygame.Rect(int(screen_x),int(screen_y),CELL_SIZE,CELL_SIZE)
            dxp = (x*CELL_SIZE+CELL_SIZE/2)-player_x
            dyp = (y*CELL_SIZE+CELL_SIZE/2)-player_y
            dist = sqrt(dxp*dxp+dyp*dyp)
            light = max(0.2,1-dist/(CELL_SIZE*LIGHT_RADIUS))
            color = tuple(min(255,int(c*light)) for c in block_colors.get(bid,(255,0,255)))
            pygame.draw.rect(screen,color,rect)

    # Draw player
    player_screen_x = player_x - cam_offset
    player_screen_y = SCREEN[1] - (player_y + CELL_SIZE)
    player_rect = pygame.Rect(int(player_screen_x),int(player_screen_y),CELL_SIZE,CELL_SIZE)
    pygame.draw.rect(screen,(255,255,0),player_rect)

    # UI
    text = font.render(f"Selected: {block_names.get(selected_slot,'unknown')}  (1-9,Q/E/R)",True,(0,0,0))
    screen.blit(text,(10,10))

    pygame.display.flip()
