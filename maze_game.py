from custom_prim import *
import pygame
from shapely.geometry import Point, LineString
import math

def extend_line(line):
    p1, p2 = line
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    # Extending by a large factor
    return LineString([(p1[0] - 1000*dx, p1[1] - 1000*dy), (p1[0] + 1000*dx, p1[1] + 1000*dy)])

class Button:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def check_click(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, color):
        pygame.draw.rect(surface, color, self.rect)

class Ball:
    def __init__(self, pos, radius):
        self.pos = pos
        self.x, self.y = pos
        self.radius = radius
        self.center = Point(pos)
        self.circle = self.center.buffer(self.radius)
        self.speed = 10

    def update(self, pos):
        self.pos = pos
        self.center = Point(pos)
        self.circle = self.center.buffer(self.radius)

    def draw(self, surface, color):
        pygame.draw.circle(surface, color, self.pos, self.radius)


    def update_velocity(self, pos1):
        def function_speed(x):
            if x > 1:
                return (100*(math.exp(-50/(x-1))))
            else:
                return 0
        mag = math.dist(self.pos, pos1)
        direction = [a / mag for a in sub(pos1, self.pos)]
        self.speed = function_speed(mag)
        self.velocity = [a * self.speed for a in direction]

    def better_nav(self, lines):
        dimensions = 2
        collision_check = 0
        points_hit = []
        P0 = np.array([self.pos[0], self.pos[1], 0])
        V = np.array([self.velocity[0], self.velocity[1], 0])
        for i in lines:
            #if collision_check >= 2:
                #V = np.array([0, 0, 0])

            A = np.array([i[0][0], i[0][1], 0])
            B = np.array([i[1][0], i[1][1], 0])
            E = B - A
            W = P0 - A
            j = np.linalg.norm(np.cross(V, E))**2
            k = 2 * (np.dot(np.cross(W, E), np.cross(V, E)))
            l = (np.linalg.norm(np.cross(W, E))**2) - ((self.radius**2) * (np.linalg.norm(E)**2))
            if (k**2 - 4 * j * l) < 0:
                continue
            else:
                t = (-k - math.sqrt(k**2 - 4 * j * l)) / (2 * j)
                if 0 <= t <= 1:
                    phit = P0 + t * V
                    u = np.dot(phit - A, E) / np.dot(E, E) 
                    if 0 <= u <= 1:
                        n = phit - (A + (u * E))
                        n_1 = n / np.linalg.norm(n)
                        points_hit.append({"phit": phit, "normal": n_1})
                        collision_check += 1                    

        if collision_check == 0:
            self.update([P0[a] + V[a] for a in range(dimensions)])
        else:
            avg = np.array([0, 0, 0])
            minimum_point = points_hit[0]["phit"]
            min_dist = math.dist(P0, minimum_point)
            for i in points_hit:
                avg = avg + i["normal"]
                dist = math.dist(P0, i["phit"])
                if min_dist > dist:
                    min_dist = dist
                    minimum_point = i["phit"]
            avg_normal = avg / np.linalg.norm(avg)
            avg_radius = avg_normal * self.radius
            new_pos = minimum_point + avg_radius
            self.update([new_pos[a] for a in range(dimensions)])
        return

def add_mouse_queue(mouseq, pos):
    if len(mouseq) >= 2:
        mouseq.pop(0)
    mouseq.append(pos)

def update_lines(lines_1, x0, y0, width, height, scale, maze):
        lines_1.clear()
        for i in range(width):
                for j in range(height):
                    lns = get_lines(x0 + scale*i, y0 + scale*j, scale, scale, maze[j][i])
                    for l in lns:
                        lines_1.append(l)

def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1000, 1000))
    clock = pygame.time.Clock()
    running = True

    mouse_pos = []
    mouse_pos_list = []
    mouse = pygame.mouse

    restart_button = Button(100, 40, 50, 20)
    font = pygame.font.Font(None, size = 16)
    text_restart = font.render("Restart", True, "Dark Gray")
    rect_restart = text_restart.get_rect(center = restart_button.rect.center)

    width, height = 10, 10
    x0, y0 = 100, 100
    scale = 800 // width
    margin = scale // 3
    start_trigger = Button(x0 + margin, y0 + margin, scale-margin*2, scale-margin*2)
    end_trigger = Button(x0 + (width-1)*scale + margin, y0 + (height-1)*scale + margin, scale-margin*2, scale-margin*2)

    maze = create_maze(width, height)
    ball = Ball((x0 + scale/2, y0 + scale/2), 5)
    lines = []

    update_lines(lines, x0, y0, width, height, scale, maze)
    end_game = False

    while running:
        if mouse.get_focused():
            add_mouse_queue(mouse_pos, mouse.get_pos())
            if not end_game:
                ball.update_velocity(mouse.get_pos())
                ball.better_nav(lines)
        if end_trigger.check_click(ball.pos):
            end_game = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONUP:
                if restart_button.check_click(event.pos):
                    maze = create_maze(width, height)
                    ball = Ball((x0 + scale/2, y0 + scale/2), 5)
                    update_lines(lines, x0, y0, width, height, scale, maze)
                    end_game = False

        screen.fill("black")
        restart_button.draw(screen, "red")
        screen.blit(text_restart, rect_restart)
        start_trigger.draw(screen, "light green")
        end_trigger.draw(screen, "pink")
        for i in lines:
            pygame.draw.line(screen, "Dark Gray", i[0], i[1], width=2)
        if len(mouse_pos) == 2:
            pygame.draw.line(screen, "red", *mouse_pos)

        ball.draw(screen, "red")
        
        clock.tick(60)
        pygame.display.flip()

if __name__ == "__main__":
    main()