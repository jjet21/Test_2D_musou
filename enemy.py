"""
Enemy entities with FSM-based AI
"""
import pygame
import math
import random
from core.entity import Entity
from core.component import Transform, Sprite, Health, Combat, AI


class EnemyAI(AI):
    """Extended AI component for enemies"""
    def __init__(self):
        super().__init__("idle")
        self.aggro_range = 400
        self.attack_range = 40
        self.wander_speed = 50
        self.chase_speed = 120
        self.follow_flowfield = True

    def reset(self):
        """Reset AI state"""
        self.state = "idle"
        self.target = None
        self.state_timer = 0
        self.decision_timer = 0


def create_grunt(entity_manager, x, y):
    """Create a basic grunt enemy"""
    entity = entity_manager.create_entity()
    entity.add_tag("enemy")
    entity.add_tag("grunt")

    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Create sprite - MUCH BIGGER and MORE VISIBLE
    surface = pygame.Surface((48, 48), pygame.SRCALPHA)
    # Bright red body (opaque, not transparent)
    pygame.draw.circle(surface, (255, 50, 50), (24, 24), 22)
    # Black outline (very visible)
    pygame.draw.circle(surface, (0, 0, 0), (24, 24), 22, 3)
    # White eyes (big and obvious)
    pygame.draw.circle(surface, (255, 255, 255), (16, 20), 6)
    pygame.draw.circle(surface, (255, 255, 255), (32, 20), 6)
    pygame.draw.circle(surface, (0, 0, 0), (16, 20), 3)
    pygame.draw.circle(surface, (0, 0, 0), (32, 20), 3)
    # Add a health bar on top for visibility
    pygame.draw.rect(surface, (0, 0, 0), (4, 2, 40, 4))
    pygame.draw.rect(surface, (0, 255, 0), (5, 3, 38, 2))
    sprite = Sprite(surface, 48, 48)
    sprite.layer = 5  # Render on top of most things
    entity.add_component("Sprite", sprite)

    health = Health(50)
    entity.add_component("Health", health)

    combat = Combat(damage=10, attack_range=30, attack_cooldown=1.0)
    combat.team = 1  # Enemy team
    entity.add_component("Combat", combat)

    ai = EnemyAI()
    ai.chase_speed = 100
    entity.add_component("AI", ai)

    return entity


def create_officer(entity_manager, x, y):
    """Create an officer enemy (tougher, smarter)"""
    entity = entity_manager.create_entity()
    entity.add_tag("enemy")
    entity.add_tag("officer")

    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Create sprite - MUCH BIGGER and MORE VISIBLE
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    # Bright purple/magenta body (opaque)
    pygame.draw.circle(surface, (255, 0, 255), (32, 32), 30)
    # Black outline (very thick and visible)
    pygame.draw.circle(surface, (0, 0, 0), (32, 32), 30, 4)
    # Bright yellow eyes (big and obvious)
    pygame.draw.circle(surface, (255, 255, 0), (20, 28), 8)
    pygame.draw.circle(surface, (255, 255, 0), (44, 28), 8)
    pygame.draw.circle(surface, (0, 0, 0), (20, 28), 4)
    pygame.draw.circle(surface, (0, 0, 0), (44, 28), 4)
    # Large crown to indicate officer
    pygame.draw.polygon(surface, (255, 215, 0), [(16, 10), (32, 2), (48, 10), (42, 18), (32, 14), (22, 18)])
    pygame.draw.polygon(surface, (0, 0, 0), [(16, 10), (32, 2), (48, 10), (42, 18), (32, 14), (22, 18)], 2)
    # Add a health bar on top for visibility
    pygame.draw.rect(surface, (0, 0, 0), (8, 4, 48, 6))
    pygame.draw.rect(surface, (255, 215, 0), (9, 5, 46, 4))
    sprite = Sprite(surface, 64, 64)
    sprite.layer = 5  # Render on top of most things
    entity.add_component("Sprite", sprite)

    health = Health(150)
    entity.add_component("Health", health)

    combat = Combat(damage=20, attack_range=40, attack_cooldown=0.8)
    combat.team = 1  # Enemy team
    entity.add_component("Combat", combat)

    ai = EnemyAI()
    ai.chase_speed = 140
    ai.aggro_range = 500
    entity.add_component("AI", ai)

    return entity


class EnemyAISystem:
    """System to update enemy AI"""
    def __init__(self, entity_manager, flowfield):
        self.entity_manager = entity_manager
        self.flowfield = flowfield

    def update(self, dt):
        """Update all enemy AI"""
        try:
            enemies = self.entity_manager.get_entities_with_tag("enemy")
            players = self.entity_manager.get_entities_with_tag("player")

            if not players:
                return

            player = players[0]
            player_transform = player.get_component("Transform")
            if not player_transform:
                return

            player_pos = (player_transform.x, player_transform.y)

            for enemy in enemies:
                if not enemy.active:
                    continue

                # Skip dead enemies - they shouldn't think or move
                health = enemy.get_component("Health")
                if health and health.dead:
                    continue

                transform = enemy.get_component("Transform")
                ai = enemy.get_component("AI")
                combat = enemy.get_component("Combat")

                if not transform or not ai:
                    continue

                ai.update(dt)

                # Calculate distance to player
                dx = player_pos[0] - transform.x
                dy = player_pos[1] - transform.y
                distance = math.sqrt(dx*dx + dy*dy)

                # FSM logic
                if ai.state == "idle":
                    # Idle state - check for aggro
                    if distance < ai.aggro_range:
                        ai.change_state("chase")
                    else:
                        # Wander randomly
                        if ai.can_make_decision():
                            ai.reset_decision_timer()
                            # Random wander direction
                            angle = random.uniform(0, 2 * math.pi)
                            transform.vx = math.cos(angle) * ai.wander_speed
                            transform.vy = math.sin(angle) * ai.wander_speed

                elif ai.state == "chase":
                    # Chase player
                    if distance < ai.attack_range:
                        ai.change_state("attack")
                    elif distance > ai.aggro_range * 1.5:
                        # Lost aggro
                        ai.change_state("idle")
                    else:
                        # Move toward player using flow field or direct
                        if ai.follow_flowfield:
                            direction = self.flowfield.get_direction(transform.x, transform.y)
                            if direction[0] != 0 or direction[1] != 0:
                                transform.vx = direction[0] * ai.chase_speed
                                transform.vy = direction[1] * ai.chase_speed
                            else:
                                # Fallback to direct movement
                                if distance > 0:  # Prevent division by zero
                                    direction_x = dx / distance
                                    direction_y = dy / distance
                                    transform.vx = direction_x * ai.chase_speed
                                    transform.vy = direction_y * ai.chase_speed
                                else:
                                    transform.vx = 0
                                    transform.vy = 0
                        else:
                            # Direct movement
                            if distance > 0:  # Prevent division by zero
                                direction_x = dx / distance
                                direction_y = dy / distance
                                transform.vx = direction_x * ai.chase_speed
                                transform.vy = direction_y * ai.chase_speed
                            else:
                                transform.vx = 0
                                transform.vy = 0

                elif ai.state == "attack":
                    # Attack player
                    if distance > ai.attack_range * 1.5:
                        ai.change_state("chase")
                    else:
                        # Stop and attack
                        transform.vx = 0
                        transform.vy = 0

                        if combat and combat.can_attack():
                            combat.attack()
                            # Deal contact damage to player
                            # (actual damage will be handled by combat system)

                # Apply velocity
                transform.x += transform.vx * dt
                transform.y += transform.vy * dt
        except Exception as e:
            print(f"Error in EnemyAISystem.update: {e}")
            import traceback
            traceback.print_exc()
