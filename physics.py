from __future__ import annotations
import numpy as np
import pygame
import math
from shapely.geometry import Point, LineString

# 90 degrees clockwise
def normal2D(vector):
    return np.array([-vector[1], vector[0]])

class Main:
    def __init__(self, fps) -> None:
        self.fps = fps
        self.steps = 20
        self.dt = 1 / (self.fps * self.steps)
        self.gravity = np.array([0.0, 360.0])
        self.lines = [Line2D((0, 0), (1000, 0)), Line2D((1000, 1000), (-1000, 0)), Line2D((1000, 0), (0, 1000)), Line2D((0, 1000), (0, -1000))]
        self.balls:list[Ball2D] = []
        self.springs:list[Spring] = []
        self.friction = 0.001
        self.quadtree:QuadTree | None = None
        pass

    def add_polygon(self, polygon):
        for i in polygon.lines:
            self.lines.append(i)

    def add_ball(self, ball):
        self.balls.append(ball)

    def simulate(self):
        wh = pygame.display.get_window_size()
        for _ in range(self.steps):
            qt = QuadTree(Rect2D((wh[0]//2, wh[1]//2), wh[0]//2, wh[1]//2), 2)
            for i in range(len(self.balls)):
                b = self.balls[i]
                qt.insert(Point2D(b.xy[0], b.xy[1], b))
                b.simulate(qt)
            self.quadtree = qt

            for i in self.springs:
                i.simulate()

class Point2D:
    def __init__(self, x, y, data) -> None:
        self.x = x
        self.y = y
        self.data = data
        pass

class Rect2D:
    def __init__(self, center, width, height) -> None:
        self.center = center
        self.x, self.y = center
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width*2, self.height*2)
        self.rect.center = self.center
    
    def intersects(self, other: Rect2D):
        return self.rect.colliderect(other.rect)
    
    def contains(self, point:Point2D):
        return self.rect.collidepoint((point.x, point.y))

class QuadTree:
    def __init__(self, boundary:Rect2D, capacity) -> None:
        self.boundary = boundary
        self.x, self.y = boundary.x, boundary.y
        self.width, self.height = boundary.width, boundary.height
        self.capacity = capacity
        self.points:list[Point2D] = []
        self.divided = False
        #topleft, topright, bottomright, bottomleft
        self.quadtrees = []

    def divide(self):
        self.divided = True
        topleft = QuadTree(Rect2D((self.x - self.width/2, self.y - self.height/2), self.width/2, self.height/2), self.capacity)
        topright = QuadTree(Rect2D((self.x + self.width/2, self.y - self.height/2), self.width/2, self.height/2), self.capacity)
        bottomright = QuadTree(Rect2D((self.x + self.width/2, self.y + self.height/2), self.width/2, self.height/2), self.capacity)
        bottomleft = QuadTree(Rect2D((self.x - self.width/2, self.y + self.height/2), self.width/2, self.height/2), self.capacity)
        self.quadtrees = [topleft, topright, bottomright, bottomleft]
    
    def insert(self, point):
        if self.boundary.contains(point) == False:
            return
        if len(self.points) < self.capacity:
            self.points.append(point)
        else:
            if not self.divided:
                self.divide()
            for i in self.quadtrees:
                i.insert(point)

    def query(self, range:Rect2D, point_list:list[Point2D]):
        if self.boundary.intersects(range):
            for p in self.points:
                point_list.append(p)
            if self.divided:
                for qt in self.quadtrees:
                    qt.query(range, point_list)
            return True
        else:
            return False
    
    def show(self, surface):
        pygame.draw.rect(surface, "white", self.boundary.rect, width = 2)
        if self.divided:
            for i in self.quadtrees:
                i.show(surface)

class Line2D:
    def __init__(self, point, direction) -> None:
        self.xy = np.array(point, dtype=float)
        self.x, self.y = point
        self.direction = np.array(direction)
        self.direction_norm = self.direction / np.linalg.norm(self.direction)
        self.dx, self.dy = direction
        self.normal = np.array([-self.dy, self.dx]) / np.linalg.norm(self.direction)
        pass

    @classmethod
    def from_2_points(cls, p1, p2):
        return cls(p1, [b-a for a, b in zip(p1, p2)])
    
    def draw(self, surface, color, width):
        pygame.draw.line(surface, color, [*self.xy], [*(self.xy + self.direction)], width=width)

class Polygon:
    def __init__(self, points:list) -> None:
        self.points = points
        self.lines = [Line2D.from_2_points(self.points[a], self.points[(a+1)%len(self.points)]) for a in range(len(self.points))]
        pass

    def draw(self, surface, color):
        pygame.draw.polygon(surface, color, self.points)

class Ball2D:
    def __init__(self, main:Main, start_xy:list | tuple, radius:float) -> None:
        self.main = main
        self.xy = np.array(start_xy)
        self.radius = radius
        self.velocity = np.array([0.0 for _ in range(len(self.xy))])
        self.restitution = 0.99
    
    def simulate(self, qt:QuadTree):
        self.velocity += self.main.gravity * self.main.dt
        for line in self.main.lines:
            self.line_collision(line)
        points = []
        qt.query(Rect2D([*self.xy], self.radius*2, self.radius*2), points)
        for p in points:
            if p.data is not self:
                self.ball_collision(p.data)
        
        self.xy += self.velocity * self.main.dt

    def draw(self, surface, color):
        pygame.draw.circle(surface, color, [*self.xy], self.radius)

    def line_collision(self, line):
        # first point of line to center of ball
        p = self.xy - line.xy

        # distance along first line
        distance_along_line = np.dot(self.xy - line.xy, line.direction_norm)

        # change functionality depending on the distance along the line
        if distance_along_line <= 0:
            normal = p / np.linalg.norm(p)
        elif distance_along_line >= np.linalg.norm(line.direction):
            p = self.xy - (line.xy + line.direction)
            normal = p / np.linalg.norm(p)
        else:
            normal = line.normal

        #if np.dot(self.velocity, normal) > 0:
            #normal = -normal 

        direction_norm = np.array([normal[1], -normal[0]])
        distance_from_line = np.dot(p, normal)
        
        if 0 <= distance_from_line <= self.radius:
            speed_along_normal = np.dot(self.velocity, normal)
            speed_along_tangent = np.dot(self.velocity, direction_norm)
            if speed_along_normal <= 0:
                speed_along_normal *= self.restitution
                speed_along_tangent *= 1 - self.main.friction
                temp_speed = np.array([-speed_along_normal, speed_along_tangent])
                self.velocity[0] = np.dot(temp_speed, normal)
                self.velocity[1] = np.dot(temp_speed, direction_norm)

    def ball_collision(self, other): 
        distance = np.linalg.norm(self.xy - other.xy)
        if distance > (self.radius + other.radius):
            return
        
        if distance <= (self.radius + other.radius):
            normal = (self.xy - other.xy) / distance
            tangent = np.array([normal[1], -normal[0]])
            relative_speed_along_normal = np.dot(self.velocity - other.velocity, normal)
            relative_speed_along_tangent = np.dot(self.velocity - other.velocity, tangent)
            force = relative_speed_along_tangent / 2 * tangent * self.main.friction
            force = force + (relative_speed_along_normal * normal) * self.restitution
            force = force + (relative_speed_along_normal/2 * normal) * (1 - self.restitution)
            self.velocity = self.velocity - force
            other.velocity = other.velocity + force
            if distance < (self.radius + other.radius):
                self.xy += normal * - (distance - (self.radius + other.radius)) / 2

class Spring:
    def __init__(self, main:Main, node1:Ball2D, node2:Ball2D, length = None, force = 1, damping = 0.0001, thickness = 5) -> None:
        self.main = main
        self.node1 = node1
        self.node2 = node2
        if length == None:
            length = np.linalg.norm(node1.xy - node2.xy)
        self.length = length
        self.force = force
        self.damping = damping
        self.thickness = thickness
        pass

    def simulate(self):
        displacement = self.node2.xy - self.node1.xy
        distance = np.linalg.norm(displacement)
        if distance == 0:
            return

        direction = displacement / distance
        spring_force = self.force * (distance - self.length) * direction
        relative_velocity = self.node2.velocity - self.node1.velocity
        damping_force = self.damping * np.dot(relative_velocity, direction) * direction
        total_force = spring_force + damping_force

        self.node1.velocity += total_force * self.main.dt
        self.node2.velocity -= total_force * self.main.dt 

    def draw(self, surface, color):
        pygame.draw.line(surface, color, [*self.node1.xy], [*self.node2.xy], width = self.thickness)

def loop():
    pygame.init()
    screen = pygame.display.set_mode((1000, 1000))
    clock = pygame.time.Clock()
    running = True
    main_sim = Main(60)
    my_polygon = Polygon([[200, 200], [100, 600], [300, 200]])
    main_sim.add_polygon(my_polygon)

    balls = np.zeros(shape=(4, 4), dtype=Ball2D)

    for i in range(balls.shape[1]):
        for j in range(balls.shape[0]):
            balls[j, i] = Ball2D(main_sim, (40*i + 200, 40*j + 20.0), 10)
            balls[j, i].restitution = 0.9
            main_sim.add_ball(balls[j, i])

    for index, i in np.ndenumerate(balls):
        directions = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
        for j in directions:
            try:
                y, x = index
                yd, xd = j
                ys, xs = balls.shape
                if 0 <= (y + yd) < ys and 0 <= (x + xd) < xs:
                    main_sim.springs.append(Spring(main_sim, balls[y, x], balls[y + yd, x + xd], force = 10000, damping=5, thickness=1)) # type:ignore
            except:
                pass
    
    n_spring = None
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_sim.quadtree != None:
                    points = []
                    main_sim.quadtree.query(Rect2D((event.pos[0], event.pos[1]), 10, 10), points)
                    pc = min(points, key = lambda x: math.dist([x.x, x.y], event.pos))
                    ball_pc = pc.data
                    n_ball = Ball2D(main_sim, event.pos, 1)
                    n_spring = Spring(main_sim, ball_pc, n_ball, length=0.1, force=1000, damping=1)
            if event.type == pygame.MOUSEBUTTONUP:
                n_spring = None
        if n_spring != None:
            n_spring.node2.xy = np.array(pygame.mouse.get_pos())
            main_sim.springs.append(n_spring)

        screen.fill("light blue")
        main_sim.simulate()
        if main_sim.quadtree != None:
            main_sim.quadtree.show(screen)
        for i in main_sim.balls:
            i.draw(screen, "black")
        for i in main_sim.lines:
            i.draw(screen, "green", 3)
        for i in main_sim.springs:
            i.draw(screen, "white")

        pygame.display.flip()
        if n_spring != None:
            main_sim.springs.remove(n_spring)
        clock.tick(60)

if __name__ == "__main__":
    loop()
