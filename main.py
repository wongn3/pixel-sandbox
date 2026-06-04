import pygame
from copy import deepcopy

# right now this program only does a few things:
# INPUT -> modify grid -> draw grid -> repeat 60x/sec

# setup
pygame.init()

# allows holding hotkeys down as continuous input
pygame.key.set_repeat(300, 150)

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 1200
CELL_SIZE = 2       # grid resolution
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Pixel Sandbox')
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
small_font = pygame.font.SysFont(None, 24)

GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 120) // CELL_SIZE
CANVAS_Y = 120

# how large the reaction radius is in proportion to brush size
# 1.0 = 100% brush size, 0.5 = 50% brush size, etc
REACTION_RADIUS_SCALE = 1

EMPTY = 0
SAND = 1
GRASS = 2
WATER = 3
WET_SAND = 4
MUD = 5

MATERIALS = {                                # ------ TODO ADD MATERIALS HERE ------
     EMPTY: (0, 0, 0),
     SAND: (210, 210, 100),
     GRASS: (0, 180, 90),
     WATER: (0, 60, 210),
     WET_SAND: (150, 140, 80),
     MUD: (100, 70, 40),
}

# main stores materials as ints
# this is to translate that into strings
# for all the ms
MATERIAL_ID_TO_NAME = {
     EMPTY: 'empty',
     SAND: 'sand',
     GRASS: 'grass',
     WATER: 'water',
     WET_SAND: 'wet_sand',
     MUD: 'mud',
}

# converts back to ints
MATERIAL_NAME_TO_ID = {
     'sand': SAND,
     'grass': GRASS,
     'water': WATER,
     'wet_sand': WET_SAND,
     'mud': MUD,
}

grid = [[EMPTY for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# STARTING PARAMETERS
selected_material = EMPTY
brush_size = 10
volume = 70
muted = False

# shared request counter for all file-based ms calls
# makes repeated identical requests look different to services
request_id = 0

undo_stack = []
redo_stack = []
reaction_cache = {}

show_help = False
show_reset_confirm = False
show_instructions = True

show_material_info = False
material_info_lines = []
current_info_material = None

buttons = {
     'undo': pygame.Rect(0, 0, 120, 45),
     'redo': pygame.Rect(120, 0, 120, 45),
     'reset': pygame.Rect(240, 0, 160, 45),
     'help': pygame.Rect(400, 0, 50, 45),
     'sand': pygame.Rect(35, 75, 45, 45),
     'grass': pygame.Rect(115, 75, 45, 45),
     'water': pygame.Rect(195, 75, 45, 45),
}


#####   MICROSERVICE COMMUNICATION   #####

# writes a key=value request file for a ms
# every request automatically gets a unique request_id
# example output:
# request_id=3
# material=sand
def send_request(request_file, data):
     global request_id
     request_id += 1

     with open(request_file, 'w') as file:
          file.write(f'request_id={request_id}\n')

          for key, value in data.items():
               file.write(f'{key}={value}\n')


# reads a key=value response file from a ms and returns it as a dict
# lines without '=' are ignored so malformed/blank lines dont make it crash
def read_response(response_file: str):
     data = {}

     try:
          with open(response_file, 'r') as file:
               for line in file:
                    line = line.strip()
                    if '=' not in line: continue

                    key, value = line.split('=', 1)
                    data[key] = value
     except FileNotFoundError: return None
     return data


# sends current volume and brush size to the validation ms
# the service clamps invalid values and returns new_volume/new_brush_size
# a short wait is needed because the ms checks the text file every .1 seconds
def validate_settings():
     global volume, brush_size

     send_request('validation_request.txt', {
          'volume': volume,
          'brush_size': brush_size
     })

     # tiny delay (20ms) so the validation has time to respond 
     pygame.time.wait(120)

     response = read_response('validation_response.txt')

     if response is None: return
     if 'new_volume' in response: 
          volume = int(response['new_volume'])
     if 'new_brush_size' in response:
          brush_size = int(response['new_brush_size'])


# requests info about 1 material from the material info ms
# later used to build the right-click material info popup
def get_material_info(material_name):
     send_request('material_info_request.txt', {
          'material': material_name
     })

     # tiny delay (20ms) so the ms has time to respond 
     pygame.time.wait(120)
     return read_response('material_info_response.txt')


# handles right-clicking material buttons
# if the same material popup is already open, close it
# if a different material is clicked, update popup with the new materials info
def show_info_for_material(material_name):
     global show_material_info, material_info_lines, current_info_material

     # if the popup is already showing this same material, close it
     if show_material_info and current_info_material == material_name:
          show_material_info = False
          current_info_material = None
          material_info_lines = []
          return

     # otherwise, get new info and update the popup
     info = get_material_info(material_name)

     if info is None:
          material_info_lines = [
               'Material info service did not respond.'
          ]
     elif info.get('status') == 'success':
          material_info_lines = [
               f"Material: {info.get('input_material', material_name)}",
               f"Category: {info.get('material_category', 'N/A')}",
               f"Description: {info.get('material_description', 'N/A')}",
          ]
     else:
          material_info_lines = [
               f"Error: {info.get('reason', 'unknown_error')}",
               f"Material: {info.get('input_material', material_name)}",
          ]

     current_info_material = material_name
     show_material_info = True


# sends 2 material names to the reaction rule ms
# returns the material id of the reaction result, or None if there is no reaction/error
def get_reaction_material(existing_material, new_material):
     existing_name = MATERIAL_ID_TO_NAME.get(existing_material)
     new_name = MATERIAL_ID_TO_NAME.get(new_material)

     if existing_name is None or new_name is None: return None

     send_request('reaction_request.txt', {
          'material_a': existing_name,
          'material_b': new_name
     })

     # reaction rules checks every .1 seconds
     pygame.time.wait(120)

     response = read_response('reaction_response.txt')

     if response is None: return None
     if response.get('status') != 'success': return None

     reaction_name = response.get('reaction')

     if reaction_name == 'none': return None
     return MATERIAL_NAME_TO_ID.get(reaction_name)


# caches reaction results so repeated material collisions dont call the ms every frame
# prevents a LOT of lag by virtue of not calling the service 60x/sec
def get_cached_reaction(existing_material, new_material):
     pair = frozenset([existing_material, new_material])

     if pair in reaction_cache: return reaction_cache[pair]

     reaction_material = get_reaction_material(existing_material, new_material)
     reaction_cache[pair] = reaction_material

     return reaction_material


#####   UTILITY   #####

def save_state():
     undo_stack.append(deepcopy(grid))
     if len(undo_stack) > 20: undo_stack.pop(0)
     redo_stack.clear()


def undo():
     global grid
     if undo_stack:
          redo_stack.append(deepcopy(grid))
          grid = undo_stack.pop()


def redo():
     global grid
     if redo_stack:
          undo_stack.append(deepcopy(grid))
          grid = redo_stack.pop()


def clear_grid():
     global grid
     save_state()
     grid = [[EMPTY for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]


#####   GUI/USER INPUT   #####

def draw_text(text, x, y, color=(255, 255, 255), fnt=font):
     img = fnt.render(text, True, color)
     screen.blit(img, (x, y))


def apply_brush(mx, my, material):                     # ------ TODO FUTURE PHYSICS HERE ------
     # convert mouse coordinates -> grid position
     gx = mx // CELL_SIZE
     gy = (my - CANVAS_Y) // CELL_SIZE

     # prevents out of bounds
     if not (0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT): return

     existing_material = grid[gy][gx]
     reaction_material = None
     reaction_radius = max(1, int(brush_size * REACTION_RADIUS_SCALE))

     # loop over brush area
     for dy in range(-brush_size, brush_size + 1):
          for dx in range(-brush_size, brush_size + 1):
               # skip cells outside the circle
               # COMMENT OUT THIS LINE FOR SQUARE BRUSH
               if dx * dx + dy * dy > brush_size * brush_size: continue

               nx = gx + dx   # new x
               ny = gy + dy   # new y

               # another bounds check for brush edges
               if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    existing_material = grid[ny][nx]

                    inside_reaction_radius = (
                         dx * dx + dy * dy <= reaction_radius * reaction_radius
                    )

                    if (
                         inside_reaction_radius
                         and material != EMPTY
                         and existing_material != EMPTY
                         and existing_material != material
                    ):
                         reaction_material = get_cached_reaction(existing_material, material)

                         if reaction_material is not None: 
                              grid[ny][nx] = reaction_material
                         else: grid[ny][nx] = material

                    else: grid[ny][nx] = material


def draw_button(rect, label):
    pygame.draw.rect(screen, (0, 0, 0), rect)
    pygame.draw.rect(screen, (80, 80, 80), rect, 3)
    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))


def draw_ui():
     screen.fill((0, 0, 0))

     # top utility buttons
     draw_button(buttons['undo'], 'Undo')
     draw_button(buttons['redo'], 'Redo')
     draw_button(buttons['reset'], 'Reset')
     draw_button(buttons['help'], '?')

     # toolbar area
     pygame.draw.rect(screen, (80, 80, 80), (0, 45, SCREEN_WIDTH, 75), 3)

     draw_text('Sand', 30, 50)
     draw_text('Grass', 105, 50)
     draw_text('Water', 185, 50)

     if show_instructions:
          instruction_lines = [
               'Select a material above and click anywhere to place it!',
               'Create and observe material interactions!',
               'Experiment freely, undo anytime!'
          ]

          start_y = 250
          spacing = 50
          for i, line in enumerate(instruction_lines):
               text_surface = small_font.render(line, True, (255, 255, 255))
               y = start_y + i * spacing
               screen.blit(text_surface, text_surface.get_rect(center=(SCREEN_WIDTH // 2, y)))

     # material boxes
     pygame.draw.rect(screen, MATERIALS[SAND], buttons['sand'])
     pygame.draw.rect(screen, MATERIALS[GRASS], buttons['grass'])
     pygame.draw.rect(screen, MATERIALS[WATER], buttons['water'])

     pygame.draw.rect(screen, (100, 100, 100), buttons['sand'], 4)
     pygame.draw.rect(screen, (100, 100, 100), buttons['grass'], 4)
     pygame.draw.rect(screen, (100, 100, 100), buttons['water'], 4)

     # selected highlight
     if selected_material == SAND:
          pygame.draw.rect(screen, (255, 0, 0), buttons['sand'], 5)
     elif selected_material == GRASS:
          pygame.draw.rect(screen, (255, 0, 0), buttons['grass'], 5)
     elif selected_material == WATER:
          pygame.draw.rect(screen, (255, 0, 0), buttons['water'], 5)

     # canvas border
     pygame.draw.rect(screen, (80, 80, 80), (0, CANVAS_Y, SCREEN_WIDTH, SCREEN_HEIGHT - CANVAS_Y), 3)


def draw_grid():
     for y in range(GRID_HEIGHT):
          for x in range(GRID_WIDTH):
               material = grid[y][x]
               if material != EMPTY:
                    pygame.draw.rect(
                         screen,
                         MATERIALS[material],
                         (x * CELL_SIZE, CANVAS_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    )


#####   POPUPS   #####

def draw_help_popup():
     box = pygame.Rect(220, 210, 360, 210)
     pygame.draw.rect(screen, (0, 0, 0), box)
     pygame.draw.rect(screen, (100, 100, 100), box, 3)

     lines = [
          '1. Select a material above',
          '2. Left click/hold to place pixels',
          '3. Right click/hold to erase',
          '4. Undo/Redo to fix mistakes',
          '5. Reset to clear canvas'
     ]

     y = 235
     for line in lines:
          draw_text(line, 245, y, (255, 255, 255), small_font)
          y += 32


def draw_reset_popup():
     box = pygame.Rect(190, 230, 420, 120)
     pygame.draw.rect(screen, (0, 0, 0), box)
     pygame.draw.rect(screen, (100, 100, 100), box, 3)

     draw_text('This will clear all pixels. Continue?', 220, 255, (255, 255, 255), small_font)

     ok_rect = pygame.Rect(190, 305, 210, 45)
     cancel_rect = pygame.Rect(400, 305, 210, 45)

     draw_button(ok_rect, 'OK')
     draw_button(cancel_rect, 'Cancel')

     return ok_rect, cancel_rect


def draw_material_info_popup():
     box = pygame.Rect(190, 390, 700, 150)
     pygame.draw.rect(screen, (0, 0, 0), box)
     pygame.draw.rect(screen, (100, 100, 100), box, 3)

     y = 415
     for line in material_info_lines:
          draw_text(line, 215, y, (255, 255, 255), small_font)
          y += 30


#####   GAME LOOP   #####

running = True
mouse_was_down = False

while running:
     left, _, right = pygame.mouse.get_pressed()
     mx, my = pygame.mouse.get_pos()

     for event in pygame.event.get():
          if event.type == pygame.QUIT: running = False

          # HOTKEYS:
          # [ decreases brush size
          # ] increases brush size
          # up increases volume
          # down decreases volume
          # values are sent to the validation ms for bounds
          if event.type == pygame.KEYDOWN:
               if event.key == pygame.K_LEFTBRACKET:
                    brush_size -= 1
                    validate_settings()
               elif event.key == pygame.K_RIGHTBRACKET:
                    brush_size += 1
                    validate_settings()
               elif event.key == pygame.K_UP:
                    volume += 1
                    validate_settings()
               elif event.key == pygame.K_DOWN:
                    volume -= 1
                    validate_settings()

          if event.type == pygame.MOUSEBUTTONDOWN:
               show_instructions = False

               if buttons['undo'].collidepoint(mx, my): undo()
               elif buttons['redo'].collidepoint(mx, my): redo()
               elif buttons['reset'].collidepoint(mx, my): show_reset_confirm = True
               elif buttons['help'].collidepoint(mx, my): show_help = not show_help

               # left-click material buttons selects the corresponding material
               # right-click material buttons request info from the material info ms
               elif buttons['sand'].collidepoint(mx, my):
                    if event.button == 1:                        # event.button == 1 is left click
                         selected_material = SAND
                         send_request('audio_request.txt', {
                              'event': 'button_clicked',
                              'button_type': 'sand',
                              'volume': volume,
                              'muted': str(muted).lower()
                         })
                    elif event.button == 3: show_info_for_material('sand')      # event.button == 3 is right click

               elif buttons['grass'].collidepoint(mx, my):
                    if event.button == 1:
                         selected_material = GRASS
                         send_request('audio_request.txt', {
                              'event': 'button_clicked',
                              'button_type': 'grass',
                              'volume': volume,
                              'muted': str(muted).lower()
                         })
                    elif event.button == 3: show_info_for_material('grass')

               elif buttons['water'].collidepoint(mx, my):
                    if event.button == 1:
                         selected_material = WATER
                         send_request('audio_request.txt', {
                              'event': 'button_clicked',
                              'button_type': 'water',
                              'volume': volume,
                              'muted': str(muted).lower()
                         })
                    elif event.button == 3: show_info_for_material('water')
               
               elif show_reset_confirm: pass
               elif my >= CANVAS_Y: save_state()

          if event.type == pygame.MOUSEBUTTONUP: mouse_was_down = False

     if show_reset_confirm:
          ok_rect, cancel_rect = pygame.Rect(190, 305, 210, 45), pygame.Rect(400, 305, 210, 45)
          if pygame.mouse.get_pressed()[0]:
               if ok_rect.collidepoint(mx, my):
                    clear_grid()
                    show_reset_confirm = False
               elif cancel_rect.collidepoint(mx, my):
                    show_reset_confirm = False
     elif my >= CANVAS_Y:
          if left: apply_brush(mx, my, selected_material)
          elif right: apply_brush(mx, my, EMPTY)

     draw_ui()
     draw_grid()

     if show_help: draw_help_popup()
     if show_reset_confirm: draw_reset_popup()
     if show_material_info: draw_material_info_popup()

     pygame.display.flip()
     clock.tick(FPS)


files_to_clear = [
    'audio_request.txt',
    'audio_response.txt',
    'validation_request.txt',
    'validation_response.txt',
    'material_info_request.txt',
    'material_info_response.txt',
    'reaction_request.txt',
    'reaction_response.txt',
]

# resets the txt files for next play
for filename in files_to_clear:
    open(filename, "w").close()
pygame.quit()