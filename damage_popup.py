"""
Damage popup system for floating damage numbers
"""
import pygame


class DamagePopup:
    """Floating damage number that rises and fades"""
    def __init__(self, pos, value, color=(255, 220, 100)):
        self.pos = pygame.Vector2(pos)
        self.value = str(value)
        self.color = color
        self.lifetime = 0.8
        self.age = 0.0
        self.vel = pygame.Vector2(0, -60)
        self.alive = True

    def update(self, dt):
        """Update position and check lifetime"""
        self.pos += self.vel * dt
        self.age += dt
        if self.age >= self.lifetime:
            self.alive = False

    def draw(self, surf, font, camera_offset=(0, 0)):
        """Draw popup with alpha fade"""
        if not self.alive:
            return
        alpha = int(255 * (1 - self.age / self.lifetime))
        text = font.render(self.value, True, self.color)
        text.set_alpha(alpha)
        screen_pos = (self.pos.x - camera_offset[0], self.pos.y - camera_offset[1])
        surf.blit(text, screen_pos)


class PopupSystem:
    """Manages damage popups"""
    def __init__(self):
        self.popups = []
        self.font = pygame.font.SysFont(None, 24)

    def spawn(self, pos, value, color=(255, 220, 100)):
        """Spawn a damage popup at position"""
        self.popups.append(DamagePopup(pos, value, color))

    def update(self, dt):
        """Update all popups and remove dead ones"""
        for p in self.popups:
            p.update(dt)
        self.popups = [p for p in self.popups if p.alive]

    def draw(self, surf, camera_offset=(0, 0)):
        """Draw all popups"""
        for p in self.popups:
            p.draw(surf, self.font, camera_offset)
