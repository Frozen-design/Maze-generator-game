import numpy as np
import pygame
import math

class Main:
    def __init__(self, fps) -> None:
        self.fps = fps
        self.steps = 10
        self.dt = 1 / (self.fps * self.steps)
        self.gravity = np.array([0.0, 360.0])
        self.lines = [Line2D((0, 0), (1000, 0)), Line2D((1000, 1000), (-1000, 0)), Line2D((1000, 0), (0, 1000)), Line2D((0, 1000), (0, -1000))]
        self.balls = []
        self.springs = []
        self.friction = 0.001
        pass

    def add_polygon(self, polygon):
        for i in polygon.lines:
            self.lines.append(i)

    def add_ball(self, ball):
        self.balls.append(ball)

    def simulate(self):
        for _ in range(self.steps):
            for i in range(len(self.balls)):
                self.balls[i].simulate()

            for i in self.springs:
                i.simulate()

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

        pass
    
    def simulate(self):
        
        self.velocity += self.main.gravity * self.main.dt
        for line in self.main.lines:
            self.line_collision(line)
        for ball in self.main.balls:
            if ball is not self:
                self.ball_collision(ball)
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

        if np.dot(self.velocity, normal) > 0:
            normal = -normal 

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
    my_polygon = Polygon([[200, 200], [100, 600], [500, 800], [300, 200]])
    main_sim.add_polygon(my_polygon)
    for i in range(25):
        main_sim.add_ball(Ball2D(main_sim, (22*i+20, 100.0), 10))

    for i in range(len(main_sim.balls)-1):
        main_sim.springs.append(Spring(main_sim, main_sim.balls[i], main_sim.balls[i + 1], force = 10000))
    

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill("light blue")
        main_sim.simulate()
        for i in main_sim.balls:
            i.draw(screen, "black")
        for i in main_sim.lines:
            i.draw(screen, "green", 3)
        for i in main_sim.springs:
            i.draw(screen, "white")

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    loop()
