"""
Player entity and control system
"""
import pygame
import math
from core.entity import Entity
from core.component import Transform, Sprite, Health, Combat


class PlayerController:
    """Component for player input handling"""
    def __init__(self):
        self.move_speed = 250
        self.dash_speed = 600
        self.dash_duration = 0.2
        self.dash_cooldown = 1.0

        # Dash state
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = pygame.math.Vector2(0, 0)

        # Attack state
        self.light_attack_cooldown = 0.3
        self.heavy_attack_cooldown = 0.8
        self.musou_cooldown = 10.0

        self.light_attack_timer = 0
        self.heavy_attack_timer = 0
        self.musou_timer = 0
        self.musou_energy = 100
        self.max_musou_energy = 100

        # Invincibility frames
        self.invincible = False
        self.invincible_duration = 0

    def update(self, dt):
        """Update timers"""
        # Cooldown timers
        if self.light_attack_timer > 0:
            self.light_attack_timer -= dt
        if self.heavy_attack_timer > 0:
            self.heavy_attack_timer -= dt
        if self.musou_timer > 0:
            self.musou_timer -= dt
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        # Dash state
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.invincible = False

        # Invincibility frames
        if self.invincible and not self.is_dashing:
            self.invincible_duration -= dt
            if self.invincible_duration <= 0:
                self.invincible = False

        # Regenerate Musou energy
        if self.musou_energy < self.max_musou_energy:
            self.musou_energy = min(self.max_musou_energy, self.musou_energy + 5 * dt)

    def can_light_attack(self):
        return self.light_attack_timer <= 0 and not self.is_dashing

    def can_heavy_attack(self):
        return self.heavy_attack_timer <= 0 and not self.is_dashing

    def can_musou(self):
        return self.musou_energy >= self.max_musou_energy and self.musou_timer <= 0

    def can_dash(self):
        return self.dash_cooldown_timer <= 0 and not self.is_dashing

    def start_dash(self, direction):
        """Start dash with invincibility"""
        if self.can_dash():
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.dash_cooldown_timer = self.dash_cooldown
            self.dash_direction = direction.normalize() if direction.length() > 0 else pygame.math.Vector2(1, 0)
            self.invincible = True
            return True
        return False

    def trigger_light_attack(self):
        if self.can_light_attack():
            self.light_attack_timer = self.light_attack_cooldown
            return True
        return False

    def trigger_heavy_attack(self):
        if self.can_heavy_attack():
            self.heavy_attack_timer = self.heavy_attack_cooldown
            return True
        return False

    def trigger_musou(self):
        if self.can_musou():
            self.musou_timer = self.musou_cooldown
            self.musou_energy = 0
            return True
        return False


def create_player(entity_manager, x, y):
    """Factory function to create player entity"""
    entity = entity_manager.create_entity()
    entity.add_tag("player")

    # Components
    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Create player sprite - bright and distinct
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    # Bright cyan/blue body
    pygame.draw.circle(surface, (0, 200, 255), (20, 20), 18)
    # White outline
    pygame.draw.circle(surface, (255, 255, 255), (20, 20), 18, 3)
    # Center indicator
    pygame.draw.circle(surface, (255, 255, 255), (20, 20), 4)
    sprite = Sprite(surface, 40, 40)
    sprite.layer = 10  # Render player above enemies
    entity.add_component("Sprite", sprite)

    health = Health(200)
    entity.add_component("Health", health)

    combat = Combat(damage=30, attack_range=60, attack_cooldown=0.3)
    combat.team = 0  # Player team
    entity.add_component("Combat", combat)

    controller = PlayerController()
    entity.add_component("PlayerController", controller)

    return entity


class PlayerInputSystem:
    """System to handle player input"""
    def __init__(self, entity_manager, input_manager=None):
        self.entity_manager = entity_manager
        self.input_manager = input_manager

    def update(self, dt):
        """Process player input"""
        players = self.entity_manager.get_entities_with_tag("player")
        if not players:
            return

        player = players[0]
        transform = player.get_component("Transform")
        controller = player.get_component("PlayerController")
        health = player.get_component("Health")

        if not transform or not controller or not health:
            return

        # Apply invincibility to health
        health.invulnerable = controller.invincible

        # Handle dash
        if controller.is_dashing:
            # Move in dash direction
            transform.vx = controller.dash_direction.x * controller.dash_speed
            transform.vy = controller.dash_direction.y * controller.dash_speed
        else:
            # Normal movement - use InputManager if available, otherwise fallback to WASD
            if self.input_manager:
                self.input_manager.update()
                move_dir = self.input_manager.get_movement_vector()
            else:
                # Fallback to WASD + arrows
                keys = pygame.key.get_pressed()
                move_dir = pygame.math.Vector2(0, 0)

                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    move_dir.y -= 1
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    move_dir.y += 1
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    move_dir.x -= 1
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    move_dir.x += 1

            # Normalize and apply speed
            if move_dir.length() > 0:
                move_dir = move_dir.normalize()
                transform.vx = move_dir.x * controller.move_speed
                transform.vy = move_dir.y * controller.move_speed
            else:
                transform.vx = 0
                transform.vy = 0

            # Dash input
            if self.input_manager:
                if self.input_manager.is_action_pressed("dash") and move_dir.length() > 0:
                    controller.start_dash(move_dir)
            else:
                # Fallback
                keys = pygame.key.get_pressed()
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and move_dir.length() > 0:
                    controller.start_dash(move_dir)

        # Apply velocity
        transform.x += transform.vx * dt
        transform.y += transform.vy * dt

        # Update controller
        controller.update(dt)


class PlayerAttackSystem:
    """System to handle player attacks"""
    def __init__(self, entity_manager, input_manager=None):
        self.entity_manager = entity_manager
        self.input_manager = input_manager
        self.pending_attacks = []

    def update(self, dt):
        """Process player attacks"""
        players = self.entity_manager.get_entities_with_tag("player")
        if not players:
            return

        player = players[0]
        transform = player.get_component("Transform")
        controller = player.get_component("PlayerController")
        combat = player.get_component("Combat")

        if not transform or not controller or not combat:
            return

        # Light attack
        if self.input_manager:
            if self.input_manager.is_action_pressed("light_attack"):
                if controller.trigger_light_attack():
                    self.create_attack(player, "light")
        else:
            # Fallback
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                if controller.trigger_light_attack():
                    self.create_attack(player, "light")

        # Heavy attack
        if self.input_manager:
            if self.input_manager.is_action_pressed("heavy_attack"):
                if controller.trigger_heavy_attack():
                    self.create_attack(player, "heavy")
        else:
            # Fallback
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            if keys[pygame.K_LCTRL] or mouse_buttons[2]:
                if controller.trigger_heavy_attack():
                    self.create_attack(player, "heavy")

        # Musou attack
        if self.input_manager:
            if self.input_manager.is_action_pressed("musou_attack"):
                if controller.trigger_musou():
                    self.create_attack(player, "musou")
        else:
            # Fallback
            keys = pygame.key.get_pressed()
            if keys[pygame.K_m]:
                if controller.trigger_musou():
                    self.create_attack(player, "musou")

    def create_attack(self, player, attack_type):
        """Create an attack entity"""
        transform = player.get_component("Transform")
        combat = player.get_component("Combat")

        if attack_type == "light":
            damage = combat.damage
            radius = combat.attack_range
            duration = 0.2
        elif attack_type == "heavy":
            damage = combat.damage * 2
            radius = combat.attack_range * 1.5
            duration = 0.4
        elif attack_type == "musou":
            damage = combat.damage * 5
            radius = combat.attack_range * 3
            duration = 1.0
        else:
            return

        self.pending_attacks.append({
            'position': (transform.x, transform.y),
            'damage': damage,
            'radius': radius,
            'duration': duration,
            'type': attack_type,
            'team': 0  # Player team
        })
