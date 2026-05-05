from custom_prim import *
import pygame
from shapely.geometry import Point, LineString
import math

def extend_line(line):
    p1, p2 = line
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    # Extending by a large factor
    return LineString([(p1[0] - 1000*dx, p1[1] - 1000*dy),
                        (p1[0] + 1000*dx, p1[1] + 1000*dy)])

class Button:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height

    def check_click(self, pos):
        return self.x < pos[0] < self.x + self.width and self.y < pos[1] < self.y + self.height

    def draw(self, surface, color):
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))

class Ball:
    def __init__(self, pos, radius):
        self.pos = pos
        self.x, self.y = pos
        self.radius = radius
        self.center = Point(pos)
        self.circle = self.center.buffer(self.radius)
        self.speed = 10

    def draw(self, surface, color):
        pygame.draw.circle(surface, color, self.pos, self.radius)

    def line_collision(self, line):
        line = LineString(line)
        self.center = Point(self.pos)
        self.circle = self.center.buffer(self.radius)
        intersection = line.intersection(self.circle)
        if intersection:
            return True
        else:
            return False

    def update_velocity(self, pos1):
        def function_speed(x):
            if x > 1:
                return (10*(math.exp(-10/(x-1))))
            else:
                return 0
        mag = math.dist(self.pos, pos1)
        direction = [a / mag for a in sub(pos1, self.pos)]
        self.speed = function_speed(mag)
        self.velocity = [a * self.speed for a in direction]

    def maze_nav(self, mp, lines):
        self.update_velocity(mp)
        pos = add(self.pos, self.velocity)
        ball = Ball(pos, self.radius)
        if not any([ball.line_collision(a) for a in lines]):
            self.pos = pos

    # if position is across a line, set final position to on the line
    # then if collision:
    #   get normal vector of line
    #   copy and move line by radius * normal vector
    #   treat line like infinite line
    #   move ball to intersection 
    def better_nav(self, lines):
        pos = add(self.pos, self.velocity)
        motion = LineString([self.pos, pos])

        # Find every line that the motion of the ball intersects with
        colliding_points = []
        line_indices = []
        for index, a in enumerate(lines):
            line_a = LineString(a)
            collision_point = motion.intersection(line_a)
            if collision_point and isinstance(collision_point, Point):
                colliding_points.append([collision_point.x, collision_point.y])
                line_indices.append(index)

            
        if len(colliding_points) > 0:
            # Find the line index and closest collision point based off of the distance to the collision point. 
            min_distance = math.dist(self.pos, colliding_points[0])
            closest_point = colliding_points[0]
            line_index = line_indices[0]
            for i in range(len(colliding_points)):
                # replace stats when the distance is less than the current minimum distance
                distance = math.dist(self.pos, colliding_points[i])
                if min_distance > distance:
                    min_distance = distance
                    closest_point = colliding_points[i]
                    line_index = line_indices[i]

            # Find which line the closest intersection occurs
            collision_line = lines[line_index]
            # Find the perpendicular vector of the line
            line_normal = normal_v(collision_line)
            # Add the normal vector times the distance of the radius to the line and then extend the line to account for edge cases
            new_collision_line = extend_line([add(a, mult(line_normal, self.radius)) for a in collision_line])
            opp_collision_line = extend_line([add(a, mult(line_normal, -self.radius)) for a in collision_line])
            # Find the new position of the ball
            new_motion = LineString([self.pos, closest_point])
            if math.dist(*new_motion.coords) < self.radius:
                return
            
            # Check both sides of the line
            new_pos = new_motion.intersection(new_collision_line)
            opp_pos = new_motion.intersection(opp_collision_line)

            if new_pos and isinstance(new_pos, Point):
                self.pos = [new_pos.x, new_pos.y]
                return
            elif opp_pos and isinstance(opp_pos, Point):
                self.pos = [opp_pos.x, opp_pos.y]
                return
        else:
            self.pos = pos

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
    screen = pygame.display.set_mode((1000, 1000))
    clock = pygame.time.Clock()
    running = True

    mouse_pos = []
    mouse_pos_list = []
    mouse = pygame.mouse

    restart_button = Button(100, 40, 50, 20)

    width, height = 30, 30
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
        start_trigger.draw(screen, "light green")
        end_trigger.draw(screen, "pink")
        for i in lines:
            pygame.draw.line(screen, "white", i[0], i[1], width=2)
        if len(mouse_pos) == 2:
            pygame.draw.line(screen, "red", *mouse_pos)

        ball.draw(screen, "red")
        
        clock.tick(60)
        pygame.display.flip()

if __name__ == "__main__":
    main()