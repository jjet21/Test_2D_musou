"""
Attack entities with visual effects
"""
import pygame
from core.entity import Entity
from core.component import Transform, Sprite


def create_attack(entity_manager, x, y, radius, damage, duration, team=0, color=(255, 255, 100)):
    """Create a visual attack entity"""
    entity = entity_manager.create_entity()
    entity.add_tag("attack")
    entity.add_tag(f"team_{team}")

    # Transform at attack position
    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Create visual sprite
    size = int(radius * 2)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)

    # Draw expanding circle with glow effect
    # Outer glow (transparent)
    pygame.draw.circle(surface, (*color, 80), (radius, radius), radius)
    # Inner bright circle
    pygame.draw.circle(surface, (*color, 180), (radius, radius), int(radius * 0.7))
    # Center bright spot
    pygame.draw.circle(surface, (255, 255, 255, 200), (radius, radius), int(radius * 0.4))
    # Outline
    pygame.draw.circle(surface, color, (radius, radius), radius, 3)

    sprite = Sprite(surface, size, size)
    sprite.layer = 10  # Draw on top
    entity.add_component("Sprite", sprite)

    # Attack data component
    attack_data = AttackData(radius, damage, duration, team)
    entity.add_component("AttackData", attack_data)

    return entity


class AttackData:
    """Component holding attack information"""
    def __init__(self, radius, damage, duration, team):
        self.radius = radius
        self.damage = damage
        self.duration = duration
        self.timer = duration
        self.team = team
        self.hit_entities = set()  # Track what we've already hit

    def update(self, dt):
        """Update attack lifetime"""
        self.timer -= dt
        if self.timer <= 0:
            return False  # Attack expired
        return True

    def has_hit(self, entity_id):
        """Check if we've already hit this entity"""
        return entity_id in self.hit_entities

    def mark_hit(self, entity_id):
        """Mark entity as hit"""
        self.hit_entities.add(entity_id)


class AttackSystem:
    """System to manage attack entities and apply damage"""
    def __init__(self, entity_manager, collision_system, pool_manager=None):
        self.entity_manager = entity_manager
        self.collision_system = collision_system
        self.pool_manager = pool_manager

    def update(self, dt):
        """Update all active attacks"""
        attacks = self.entity_manager.get_entities_with_tag("attack")

        for attack in attacks:
            if not attack.active:
                continue

            attack_data = attack.get_component("AttackData")
            transform = attack.get_component("Transform")
            sprite = attack.get_component("Sprite")

            if not attack_data or not transform:
                continue

            # Update lifetime
            if not attack_data.update(dt):
                attack.destroy()
                continue

            # Update visual (fade out)
            if sprite and sprite.surface:
                alpha = int((attack_data.timer / attack_data.duration) * 255)
                sprite.surface.set_alpha(alpha)

            # Check for hits
            nearby = self.collision_system.spatial_hash.query_radius(
                transform.x, transform.y, attack_data.radius
            )

            # AttackSystem is VISUAL ONLY - damage is handled by CombatSystem
            # This system just manages attack entity lifetime and visuals
            # No damage logic here to prevent double-damage bug
