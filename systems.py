"""
Game systems (rendering, combat, etc.)
"""
import pygame
from core.engine import System


class RenderSystem(System):
    """Renders all entities with sprites"""
    def __init__(self, entity_manager, screen, camera_offset=(0, 0)):
        super().__init__(entity_manager)
        self.screen = screen
        self.camera_x = 0
        self.camera_y = 0
        self.show_debug = False  # Toggle via engine.show_debug

    def update(self, dt):
        """Render all visible sprites"""
        # Get all entities with sprites
        sprites = []

        for entity in self.entity_manager.entities:
            if not entity.active:
                continue

            # Skip dead entities to prevent rendering corpses
            health = entity.get_component("Health")
            if health and health.dead:
                continue

            sprite_comp = entity.get_component("Sprite")
            transform = entity.get_component("Transform")

            if sprite_comp and transform and sprite_comp.visible:
                sprites.append((entity, sprite_comp, transform))

        # Sort by layer
        sprites.sort(key=lambda x: x[1].layer)

        # Draw sprites
        for entity, sprite_comp, transform in sprites:
            # Skip if surface is None
            if sprite_comp.surface is None:
                continue

            # Validate transform position - accept both Python and numpy numeric types
            try:
                # Try to convert to float - this works for int, float, numpy.float32, numpy.float64, etc.
                x_val = float(transform.x)
                y_val = float(transform.y)
            except (TypeError, ValueError):
                continue

            # Check for NaN or inf
            import math
            if math.isnan(x_val) or math.isnan(y_val) or math.isinf(x_val) or math.isinf(y_val):
                continue

            # Use round() instead of int() for smoother sub-pixel rendering
            screen_x = round(x_val - self.camera_x - sprite_comp.width / 2)
            screen_y = round(y_val - self.camera_y - sprite_comp.height / 2)
            self.screen.blit(sprite_comp.surface, (screen_x, screen_y))

    def set_camera(self, x, y):
        """Set camera position"""
        self.camera_x = x
        self.camera_y = y


class CombatSystem(System):
    """Handles combat and damage"""
    def __init__(self, entity_manager, collision_system, pool_manager=None, particle_system=None, popup_system=None, ui_system=None):
        super().__init__(entity_manager)
        self.collision_system = collision_system
        self.pool_manager = pool_manager
        self.particle_system = particle_system
        self.popup_system = popup_system
        self.ui_system = ui_system
        self.pending_attacks = []
        self.hitstop_enabled = True  # Enable hitstop for game feel

    def add_attack(self, x, y, radius, damage, team):
        """Register an attack"""
        self.pending_attacks.append({
            'x': x,
            'y': y,
            'radius': radius,
            'damage': damage,
            'team': team
        })

    def update(self, dt):
        """Process all pending attacks"""
        hits_this_frame = False

        for attack in self.pending_attacks:
            hits = self.collision_system.check_attack_collisions(
                attack['x'],
                attack['y'],
                attack['radius'],
                attack['damage'],
                attack['team']
            )

            # Apply damage and handle hits
            for entity in hits:
                transform = entity.get_component("Transform")
                health = entity.get_component("Health")

                if transform and health:
                    # Apply damage (CollisionSystem no longer does this)
                    health.take_damage(attack['damage'])

                    # Spawn particle burst at hit location
                    if self.particle_system:
                        # Different colors for different targets
                        if entity.has_tag("enemy"):
                            color = (255, 180, 80)  # Orange for enemies
                        else:
                            color = (255, 100, 100)  # Red for player
                        self.particle_system.spawn_burst((transform.x, transform.y), color=color)

                    # Spawn damage popup
                    if self.popup_system:
                        self.popup_system.spawn((transform.x, transform.y), int(attack['damage']))

                    # Add to combo counter if player hit an enemy
                    if entity.has_tag("enemy") and attack['team'] == 0 and self.ui_system:
                        self.ui_system.add_combo()

                    hits_this_frame = True

                    # Note: Death handling is done in centralized loop below

        # Hitstop effect - tiny freeze on hit for impact feel
        if hits_this_frame and self.hitstop_enabled:
            pygame.time.delay(35)  # 35ms freeze

        self.pending_attacks.clear()

        # Handle ALL dead enemies (including those killed by AttackSystem)
        enemies = self.entity_manager.get_entities_with_tag("enemy")
        for enemy in enemies:
            if enemy.active:  # Only process active enemies
                health = enemy.get_component("Health")
                if health and health.dead:
                    # Return to pool
                    if self.pool_manager:
                        if enemy.has_tag("grunt"):
                            self.pool_manager.release("enemy_grunt", enemy)
                        elif enemy.has_tag("officer"):
                            self.pool_manager.release("enemy_officer", enemy)
                        else:
                            enemy.destroy()
                    else:
                        enemy.destroy()

        # Handle dead army units (soldiers, officers, generals)
        army_units = self.entity_manager.get_entities_with_tag("unit")
        for unit in army_units:
            if unit.active:
                health = unit.get_component("Health")
                if health and health.dead:
                    # Remove from squad assignments
                    unit_comp = unit.get_component("Unit")
                    if unit_comp and unit_comp.squad_id:
                        # Notify blackboard (handled in army_systems)
                        pass
                    # Destroy the unit (army units are not pooled)
                    unit.destroy()

        # Check for contact damage (enemies touching player)
        players = self.entity_manager.get_entities_with_tag("player")
        enemies = self.entity_manager.get_entities_with_tag("enemy")

        for player in players:
            if not player.active:
                continue

            player_transform = player.get_component("Transform")
            player_health = player.get_component("Health")

            if not player_transform or not player_health:
                continue

            # Check collision with enemies
            nearby = self.collision_system.check_entity_collisions(player, 30)

            for entity in nearby:
                if entity.has_tag("enemy") and entity.active:
                    enemy_combat = entity.get_component("Combat")
                    if enemy_combat and enemy_combat.can_attack():
                        player_health.take_damage(enemy_combat.damage)
                        enemy_combat.attack()

        # Army vs Army combat (soldiers, officers, generals fighting each other)
        self._handle_army_combat(dt)

    def _handle_army_combat(self, dt):
        """Handle combat between army units"""
        # Get all army units
        army_units = self.entity_manager.get_entities_with_tag("unit")

        for attacker in army_units:
            if not attacker.active:
                continue

            attacker_health = attacker.get_component("Health")
            if attacker_health and attacker_health.dead:
                continue

            attacker_transform = attacker.get_component("Transform")
            attacker_combat = attacker.get_component("Combat")

            if not attacker_transform or not attacker_combat:
                continue

            # Can this unit attack?
            if not attacker_combat.can_attack():
                continue

            # Find nearby enemies
            nearby = self.collision_system.check_entity_collisions(attacker, attacker_combat.attack_range)

            for defender in nearby:
                if not defender.active:
                    continue

                # Skip if not a unit or same team
                if not defender.has_tag("unit"):
                    continue

                defender_combat = defender.get_component("Combat")
                if not defender_combat or defender_combat.team == attacker_combat.team:
                    continue

                defender_health = defender.get_component("Health")
                if not defender_health or defender_health.dead:
                    continue

                # Apply morale modifier if unit has one
                damage = attacker_combat.damage
                unit_comp = attacker.get_component("Unit")
                if unit_comp:
                    damage *= unit_comp.get_combat_modifier()

                # Deal damage
                defender_health.take_damage(damage)
                attacker_combat.attack()

                # Visual feedback
                defender_transform = defender.get_component("Transform")
                if defender_transform:
                    if self.particle_system:
                        color = (255, 100, 100) if defender_combat.team == 0 else (255, 180, 80)
                        self.particle_system.spawn_burst((defender_transform.x, defender_transform.y), color=color, count=3)

                    if self.popup_system:
                        self.popup_system.spawn((defender_transform.x, defender_transform.y), int(damage))

                # Only attack once per cooldown
                break


class CameraSystem(System):
    """Manages camera following player with zoom support"""
    def __init__(self, entity_manager, render_system, screen_width, screen_height, world_width, world_height):
        super().__init__(entity_manager)
        self.render_system = render_system
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.smoothing = 0.15  # Camera smoothing factor (0 = instant, 1 = no movement)

        # Zoom support
        self.zoom_level = 1.0  # 1.0 = normal, 0.5 = zoomed out (see 4x more area)
        self.target_zoom = 1.0
        self.zoom_speed = 3.0  # Speed of zoom transition

    def handle_zoom_input(self, event):
        """Handle zoom input from mouse wheel or keyboard"""
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:  # Scroll up
                self.target_zoom = 0.5  # Zoom out
                print("[CAMERA] Zooming out (0.5x)")
            else:  # Scroll down
                self.target_zoom = 1.0  # Zoom in
                print("[CAMERA] Zooming in (1.0x)")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.target_zoom = 0.5  # Zoom out
                print("[CAMERA] Zooming out (0.5x)")
            elif event.key == pygame.K_MINUS:
                self.target_zoom = 1.0  # Zoom in
                print("[CAMERA] Zooming in (1.0x)")

    def update(self, dt):
        """Update camera to follow player with smooth zoom"""
        # Smooth zoom transition
        if abs(self.zoom_level - self.target_zoom) > 0.01:
            diff = self.target_zoom - self.zoom_level
            self.zoom_level += diff * self.zoom_speed * dt
        else:
            self.zoom_level = self.target_zoom

        players = self.entity_manager.get_entities_with_tag("player")
        if not players:
            return

        player = players[0]
        transform = player.get_component("Transform")
        if not transform:
            return

        # Adjust viewport size based on zoom
        # When zoomed out (0.5x), we see 2x more area in each dimension (4x total)
        viewport_width = self.screen_width / self.zoom_level
        viewport_height = self.screen_height / self.zoom_level

        # Calculate target camera position (centered on player)
        target_camera_x = transform.x - viewport_width / 2
        target_camera_y = transform.y - viewport_height / 2

        # Clamp to world bounds
        target_camera_x = max(0, min(target_camera_x, self.world_width - viewport_width))
        target_camera_y = max(0, min(target_camera_y, self.world_height - viewport_height))

        # Smooth camera movement (interpolate towards target)
        current_camera_x = self.render_system.camera_x
        current_camera_y = self.render_system.camera_y

        smooth_camera_x = current_camera_x + (target_camera_x - current_camera_x) * self.smoothing
        smooth_camera_y = current_camera_y + (target_camera_y - current_camera_y) * self.smoothing

        self.render_system.set_camera(smooth_camera_x, smooth_camera_y)


class UISystem(System):
    """Renders UI elements"""
    def __init__(self, entity_manager, screen):
        super().__init__(entity_manager)
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 36)
        self.combo = 0
        self.combo_timer = 0.0
        self.combo_reset_time = 1.5  # Reset combo after 1.5 seconds

    def add_combo(self):
        """Increment combo counter"""
        self.combo += 1
        self.combo_timer = self.combo_reset_time

    def reset_combo(self):
        """Reset combo counter"""
        self.combo = 0
        self.combo_timer = 0.0

    def update(self, dt):
        """Draw UI"""
        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.reset_combo()

        # Get player
        players = self.entity_manager.get_entities_with_tag("player")
        if not players:
            return

        player = players[0]
        health = player.get_component("Health")
        controller = player.get_component("PlayerController")

        if health:
            # Health bar
            bar_width = 200
            bar_height = 20
            health_percent = health.health_percent

            pygame.draw.rect(self.screen, (100, 100, 100), (10, 10, bar_width, bar_height))
            pygame.draw.rect(self.screen, (200, 50, 50),
                           (10, 10, int(bar_width * health_percent), bar_height))
            pygame.draw.rect(self.screen, (255, 255, 255), (10, 10, bar_width, bar_height), 2)

            health_text = self.font.render(
                f"HP: {int(health.current_health)}/{int(health.max_health)}",
                True, (255, 255, 255)
            )
            self.screen.blit(health_text, (220, 12))

        if controller:
            # Musou energy bar
            bar_width = 200
            bar_height = 15
            energy_percent = controller.musou_energy / controller.max_musou_energy

            pygame.draw.rect(self.screen, (50, 50, 50), (10, 40, bar_width, bar_height))
            pygame.draw.rect(self.screen, (255, 215, 0),
                           (10, 40, int(bar_width * energy_percent), bar_height))
            pygame.draw.rect(self.screen, (255, 255, 255), (10, 40, bar_width, bar_height), 2)

            musou_text = self.font.render("MUSOU", True, (255, 215, 0))
            self.screen.blit(musou_text, (220, 38))

        # Enemy count (only count active enemies)
        enemy_count = len([e for e in self.entity_manager.get_entities_with_tag("enemy") if e.active])
        enemy_text = self.font.render(f"Enemies: {enemy_count}", True, (255, 100, 100))
        self.screen.blit(enemy_text, (self.screen.get_width() - 150, 10))

        # Combo counter (center top of screen)
        if self.combo > 0:
            combo_text = self.large_font.render(f"{self.combo} HIT COMBO!", True, (255, 220, 100))
            combo_rect = combo_text.get_rect(center=(self.screen.get_width() // 2, 30))
            # Draw shadow for better visibility
            shadow_text = self.large_font.render(f"{self.combo} HIT COMBO!", True, (0, 0, 0))
            shadow_rect = shadow_text.get_rect(center=(self.screen.get_width() // 2 + 2, 32))
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(combo_text, combo_rect)
