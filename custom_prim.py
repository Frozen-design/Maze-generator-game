import random
import pygame
import numpy as np

N, E, S, W = 1, 2, 4, 8
F = 16
IN = 32

directions = [[0, -1], [1, 0], [0, 1], [-1, 0]]
cardinals = [N, E, S, W]
inverse = [S, W, N, E]

def add(ss:list, oo:list) -> list:
    return [a + b for a, b in zip(ss, oo)]

def sub(ss:list, oo:list) -> list:
    return [a - b for a, b in zip(ss, oo)]

def mult(ss:list, oo:int) -> list:
    return [a * oo for a in ss]

def normal_v(line):
    # Get segment coordinates
    p1 = np.array(line[0])
    p2 = np.array(line[1])

    # Direction vector (tangent)
    tangent = p2 - p1

    # Normal vector (rotate 90 degrees: (-y, x))
    normal = np.array([-tangent[1], tangent[0]])

    # Unit normal vector
    unit_normal = normal / np.linalg.norm(normal)

    return [a for a in unit_normal]
        
def access(grid, pos:list):
    return grid[pos[1]][pos[0]]

def get_flag(grid, pos:list, flag:int):
    try:
        return access(grid, pos) & flag
    except:
        return False

def set_flag(grid, pos:list, flag:int):
    grid[pos[1]][pos[0]] |= flag

def valid_cell(grid, pos):
    height = len(grid)
    width = len(grid[0])
    x = pos[0]
    y = pos[1]
    return 0 <= x < width and 0 <= y < height

def add_frontier(pos, grid:list, frontier:list):
    set_flag(grid, pos, IN)
    frontier.remove(pos)
    for i in range(len(directions)):
        try:
            new_cell = add(pos, directions[i])
            if valid_cell(grid, new_cell):
                set_flag(grid, new_cell, F)
                if (new_cell not in frontier) and (not get_flag(grid, new_cell, IN)):
                    frontier.append(new_cell)
        except:
            pass

def get_random_value(li:list):
    item = li[random.randint(0, len(li)-1)]
    return item

def select_rf_cell(grid, frontier:list):
    cell = get_random_value(frontier)
    add_frontier(cell, grid, frontier)
    adj = [
        {"cell": add(cell, directions[i]), "cardinal": cardinals[i], "inverse": inverse[i]} 
        for i in range(len(directions)) 
        if get_flag(grid, add(cell, directions[i]), IN) and valid_cell(grid, add(cell, directions[i]))
        ]
    in_cell = get_random_value(adj)
    set_flag(grid, cell, in_cell["cardinal"])
    set_flag(grid, in_cell["cell"], in_cell["inverse"])

def create_maze(width, height):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    first_cell = [random.randint(0, width-1), random.randint(0, height-1)]
    frontier = [first_cell]
    add_frontier(first_cell, grid, frontier)
    while frontier:
        select_rf_cell(grid, frontier)

    return grid

def step_maze(width, height, step):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    first_cell = [random.randint(0, width-1), random.randint(0, height-1)]
    frontier = [first_cell]
    add_frontier(first_cell, grid, frontier)
    for _ in range(step):
        select_rf_cell(grid, frontier)

    return grid

def draw_piece(surface, color, x, y, width, height, number):
    lines = get_lines(x, y, width, height, number)
    
    for i in lines:
        pygame.draw.line(surface, color, i[0], i[1], 3)


def get_lines(x, y, width, height, number):
    lines = []
    topleft = [x, y]
    topright = [x + width, y]
    bottomleft = [x, y + height]
    bottomright = [x + width, y + height]
    if not (number & N):
        lines.append([topleft, topright])
    if not (number & E):
        lines.append([topright, bottomright])
    if not (number & S):
        lines.append([bottomright, bottomleft])
    if not (number & W):
        lines.append([bottomleft, topleft])

    return lines


def main():
    width, height = 8, 8
    maze = create_maze(width, height)
    pygame.init()
    screen = pygame.display.set_mode((1000, 1000))
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        x0 = 100
        y0 = 100
        scale = 100
        for i in range(width):
            for j in range(height):
                draw_piece(screen, "white", x0 + scale*i, y0 + scale*j, scale, scale, maze[j][i])
        
        clock.tick(60)
        pygame.display.flip()

if __name__ == "__main__":
    main()

