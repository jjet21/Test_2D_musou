"""
Particle system for visual effects
"""
import pygame
import random


class Particle:
    """Single particle with position, velocity, color, and lifetime"""
    def __init__(self, pos, vel, color, lifetime):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.alive = True

    def update(self, dt):
        """Update particle position and check lifetime"""
        self.pos += self.vel * dt
        self.age += dt
        if self.age >= self.lifetime:
            self.alive = False

    def draw(self, surf, camera_offset=(0, 0)):
        """Draw particle with alpha fade based on age"""
        if not self.alive:
            return
        alpha = max(0, 255 * (1 - self.age / self.lifetime))
        surf_color = (*self.color, int(alpha))
        s = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(s, surf_color, (2, 2), 2)
        screen_pos = (self.pos.x - camera_offset[0], self.pos.y - camera_offset[1])
        surf.blit(s, screen_pos)


class ParticleSystem:
    """Manages particle effects"""
    def __init__(self):
        self.particles = []

    def spawn_burst(self, pos, color=(255, 200, 120), count=8, speed=180):
        """Spawn a burst of particles at position"""
        for _ in range(count):
            angle = random.uniform(0, 360)
            vel = pygame.Vector2(speed, 0).rotate(angle)
            lifetime = random.uniform(0.3, 0.6)
            self.particles.append(Particle(pos, vel, color, lifetime))

    def update(self, dt):
        """Update all particles and remove dead ones"""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surf, camera_offset=(0, 0)):
        """Draw all particles"""
        for p in self.particles:
            p.draw(surf, camera_offset)
