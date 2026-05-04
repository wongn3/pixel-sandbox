import pygame
from copy import deepcopy

# right now this program only does a few things:
# INPUT -> modify grid -> draw grid -> repeat 60x/sec

# setup
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CELL_SIZE = 2       # grid resolution
FPS = 120

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pixel Sandbox")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
small_font = pygame.font.SysFont(None, 24)

GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 120) // CELL_SIZE
CANVAS_Y = 120

EMPTY = 0
SAND = 1
GRASS = 2

# material list
MATERIALS = {                                # ------ TODO ADD MATERIALS HERE ------
     EMPTY: (0, 0, 0),
     SAND: (210, 210, 100),
     GRASS: (0, 180, 90),
}

grid = [[EMPTY for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

selected_material = EMPTY
brush_size = 10          # as it describes

undo_stack = []
redo_stack = []

show_help = False
show_reset_confirm = False
show_instructions = True

buttons = {
     "undo": pygame.Rect(0, 0, 120, 45),
     "redo": pygame.Rect(120, 0, 120, 45),
     "reset": pygame.Rect(240, 0, 160, 45),
     "help": pygame.Rect(400, 0, 50, 45),
     "sand": pygame.Rect(35, 75, 45, 45),
     "grass": pygame.Rect(115, 75, 45, 45),
}


def draw_text(text, x, y, color=(255, 255, 255), fnt=font):
     img = fnt.render(text, True, color)
     screen.blit(img, (x, y))


def save_state():
     undo_stack.append(deepcopy(grid))
     if len(undo_stack) > 20:
          undo_stack.pop(0)
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


# drawing/erasing
def apply_brush(mx, my, material):                     # ------ TODO FUTURE PHYSICS HERE ------
     # convert mouse coordinates -> grid position
     gx = mx // CELL_SIZE
     gy = (my - CANVAS_Y) // CELL_SIZE

     # prevents out of bounds
     if not (0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT): return

     # loop over brush area
     for dy in range(-brush_size, brush_size + 1):
          for dx in range(-brush_size, brush_size + 1):
               nx = gx + dx   # new x
               ny = gy + dy   # new y

               # another bounds check for brush edges
               if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    # actual write
                    grid[ny][nx] = material


def draw_button(rect, label):
    pygame.draw.rect(screen, (0, 0, 0), rect)
    pygame.draw.rect(screen, (80, 80, 80), rect, 3)
    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))


def draw_ui():
     screen.fill((0, 0, 0))

     # top utility buttons
     draw_button(buttons["undo"], "Undo")
     draw_button(buttons["redo"], "Redo")
     draw_button(buttons["reset"], "Reset")
     draw_button(buttons["help"], "?")

     # toolbar area
     pygame.draw.rect(screen, (80, 80, 80), (0, 45, SCREEN_WIDTH, 75), 3)

     draw_text("Sand", 30, 50)
     draw_text("Grass", 105, 50)

     if show_instructions:
          instruction_lines = [
               "Select a material above and click anywhere to place it!",
               "Create and observe material interactions!",
               "Experiment freely, undo anytime!"
          ]
          start_y = 250
          spacing = 50

          for i, line in enumerate(instruction_lines):
               text_surface = small_font.render(line, True, (255, 255, 255))
               y = start_y + i * spacing
               screen.blit(text_surface, text_surface.get_rect(center=(SCREEN_WIDTH // 2, y)))

     # material boxes
     pygame.draw.rect(screen, MATERIALS[SAND], buttons["sand"])
     pygame.draw.rect(screen, MATERIALS[GRASS], buttons["grass"])

     pygame.draw.rect(screen, (100, 100, 100), buttons["sand"], 4)
     pygame.draw.rect(screen, (100, 100, 100), buttons["grass"], 4)

     # selected highlight
     if selected_material == SAND:
          pygame.draw.rect(screen, (255, 0, 0), buttons["sand"], 5)
     elif selected_material == GRASS:
          pygame.draw.rect(screen, (255, 0, 0), buttons["grass"], 5)

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


def draw_help_popup():
     box = pygame.Rect(220, 210, 360, 210)
     pygame.draw.rect(screen, (0, 0, 0), box)
     pygame.draw.rect(screen, (100, 100, 100), box, 3)

     lines = [
          "1. Select a material above",
          "2. Left click/hold to place pixels",
          "3. Right click/hold to erase",
          "4. Undo/Redo to fix mistakes",
          "5. Reset to clear canvas"
     ]

     y = 235
     for line in lines:
          draw_text(line, 245, y, (255, 255, 255), small_font)
          y += 32


def draw_reset_popup():
     box = pygame.Rect(190, 230, 420, 120)
     pygame.draw.rect(screen, (0, 0, 0), box)
     pygame.draw.rect(screen, (100, 100, 100), box, 3)

     draw_text("This will clear all pixels. Continue?", 220, 255, (255, 255, 255), small_font)

     ok_rect = pygame.Rect(190, 305, 210, 45)
     cancel_rect = pygame.Rect(400, 305, 210, 45)

     draw_button(ok_rect, "OK")
     draw_button(cancel_rect, "Cancel")

     return ok_rect, cancel_rect


running = True
mouse_was_down = False

while running:
     left, _, right = pygame.mouse.get_pressed()
     mx, my = pygame.mouse.get_pos()

     for event in pygame.event.get():
          if event.type == pygame.QUIT:
               running = False

          # CONTROLS
          if event.type == pygame.KEYDOWN:
               if event.key == pygame.K_LEFTBRACKET:
                    brush_size = max(1, brush_size - 1)
               elif event.key == pygame.K_RIGHTBRACKET:
                    brush_size += 1

          if event.type == pygame.MOUSEBUTTONDOWN:
               show_instructions = False

               if buttons["undo"].collidepoint(mx, my): undo()
               elif buttons["redo"].collidepoint(mx, my):
                    redo()
               elif buttons["reset"].collidepoint(mx, my):
                    show_reset_confirm = True
               elif buttons["help"].collidepoint(mx, my):
                    show_help = not show_help
               elif buttons["sand"].collidepoint(mx, my):
                    selected_material = SAND
               elif buttons["grass"].collidepoint(mx, my):
                    selected_material = GRASS
               elif show_reset_confirm:
                    pass
               elif my >= CANVAS_Y:
                    save_state()

          if event.type == pygame.MOUSEBUTTONUP:
               mouse_was_down = False

     if show_reset_confirm:
          ok_rect, cancel_rect = pygame.Rect(190, 305, 210, 45), pygame.Rect(400, 305, 210, 45)
          if pygame.mouse.get_pressed()[0]:
               if ok_rect.collidepoint(mx, my):
                    clear_grid()
                    show_reset_confirm = False
               elif cancel_rect.collidepoint(mx, my):
                    show_reset_confirm = False

     elif my >= CANVAS_Y:
          if left:
               apply_brush(mx, my, selected_material)
          elif right:
               apply_brush(mx, my, EMPTY)

     draw_ui()
     draw_grid()

     if show_help:
          draw_help_popup()

     if show_reset_confirm:
          draw_reset_popup()

     pygame.display.flip()
     clock.tick(FPS)

pygame.quit()