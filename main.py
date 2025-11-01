"""
Main entry point for 2D Musou Game
Enhanced version with ECS, flow-field navigation, and object pooling
"""
import pygame
import sys

from core.engine import GameEngine
from core.pool import PoolManager
from core.spatial import CollisionSystem
from core.input_config import InputManager

from game.player import create_player, PlayerInputSystem, PlayerAttackSystem
from game.flowfield import FlowField
from game.objective import ObjectiveSystem
from game.systems import RenderSystem, CombatSystem, CameraSystem, UISystem
from game.menu import KeyboardConfigMenu, ControlsDisplayOverlay, PauseMenu
from game.attack import create_attack, AttackSystem
from game.particles import ParticleSystem
from game.damage_popup import PopupSystem
from game.army_systems import ArmyManager
from debug_logger import debug_logger


class MusouGame:
    """Main game class"""
    def __init__(self):
        # World settings
        self.WORLD_WIDTH = 3200
        self.WORLD_HEIGHT = 2400
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720

        # Create engine
        self.engine = GameEngine(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, "2D Musou - ECS Edition")

        # Input manager with keyboard layout support (auto-detect)
        self.input_manager = InputManager()  # Auto-detects based on system locale

        # Pool manager
        self.pool_manager = PoolManager()

        # Flow field
        self.flowfield = FlowField(self.WORLD_WIDTH, self.WORLD_HEIGHT, cell_size=64)

        # Particle and popup systems for visual polish
        self.particle_system = ParticleSystem()
        self.popup_system = PopupSystem()

        # Initialize systems
        self.init_systems()

        # Initialize entities
        self.init_entities()

        # Objectives (must be created before army system)
        self.objective_system = ObjectiveSystem(self.engine.entity_manager, self.flowfield)
        self.init_objectives()

        # Army System (replaces old spawner and enemy AI)
        self.army_manager = ArmyManager(self.engine.entity_manager, self.objective_system)
        self.army_manager.initialize_armies(self.WORLD_WIDTH, self.WORLD_HEIGHT)

        # Menus
        self.keyboard_menu = KeyboardConfigMenu(self.engine.screen, self.input_manager)
        self.controls_overlay = ControlsDisplayOverlay(self.engine.screen, self.input_manager)
        self.pause_menu = PauseMenu(self.engine.screen)
        self.paused = False

        # Debug
        self.show_flowfield = False
        self.debug_enemy_state = False
        self.debug_logging = False  # F6 to toggle debug file logging  # Set to True to debug enemy visibility issues

    def init_systems(self):
        """Initialize all game systems"""
        # Rendering
        self.render_system = RenderSystem(
            self.engine.entity_manager,
            self.engine.screen
        )

        # Collision
        self.collision_system = CollisionSystem(self.engine.entity_manager, cell_size=100)

        # UI (create early so combat system can reference it for combo)
        self.ui_system = UISystem(self.engine.entity_manager, self.engine.screen)

        # Combat (pass pool_manager, particles, popups, and ui for visual polish)
        self.combat_system = CombatSystem(
            self.engine.entity_manager,
            self.collision_system,
            self.pool_manager,
            self.particle_system,
            self.popup_system,
            self.ui_system
        )

        # Camera
        self.camera_system = CameraSystem(
            self.engine.entity_manager,
            self.render_system,
            self.SCREEN_WIDTH,
            self.SCREEN_HEIGHT,
            self.WORLD_WIDTH,
            self.WORLD_HEIGHT
        )

        # Player (with input manager)
        self.player_input_system = PlayerInputSystem(self.engine.entity_manager, self.input_manager)
        self.player_attack_system = PlayerAttackSystem(self.engine.entity_manager, self.input_manager)

        # Attack system with visuals (pass pool_manager so enemies can be returned to pool)
        self.attack_system = AttackSystem(self.engine.entity_manager, self.collision_system, self.pool_manager)

        # Add systems to engine (order matters!)
        # Note: Army AI is NOT added here - it's updated separately in game loop
        self.engine.add_system(self.player_input_system)
        self.engine.add_system(self.player_attack_system)
        self.engine.add_system(self.attack_system)  # Process attacks
        self.engine.add_system(self.combat_system)  # Handle deaths FIRST
        self.engine.add_system(self.collision_system)  # Then rebuild spatial hash
        self.engine.add_system(self.camera_system)

    def init_entities(self):
        """Initialize game entities"""
        # Create player as soldier
        self.player = create_player(
            self.engine.entity_manager,
            self.WORLD_WIDTH // 2,
            self.WORLD_HEIGHT // 2
        )

        # Note: Army units are created by ArmyManager, not here

    def init_objectives(self):
        """Initialize bases and objectives"""
        # Add bases with strategic placement (encourages flanking)
        self.objective_system.add_base("Top Left Base", 400, 600, radius=120)
        self.objective_system.add_base("Top Right Base", 2800, 600, radius=120)
        self.objective_system.add_base("Bottom Left Base", 400, 1800, radius=120)
        self.objective_system.add_base("Bottom Right Base", 2800, 1800, radius=120)
        self.objective_system.add_base("Center Base", 1600, 1200, radius=150)

    def run(self):
        """Main game loop with custom updates"""
        self.engine.running = True

        while self.engine.running:
            try:
                dt = self.engine.clock.tick(self.engine.fps) / 1000.0

                # Handle events
                self.handle_events()

                # Sync debug flag with render system
                self.render_system.show_debug = self.engine.show_debug

                # Debug logging (F6)
                if self.debug_logging:
                    debug_logger.log_frame_start()
                    debug_logger.log_player_state(self.engine.entity_manager)

                # Skip game updates if paused or in menu
                if not self.paused and not self.keyboard_menu.active:
                    # Update flowfield
                    try:
                        self.flowfield.update(dt)
                    except Exception as e:
                        print(f"Error in flowfield.update: {e}")

                    # Update objectives
                    try:
                        self.objective_system.update(dt)
                    except Exception as e:
                        print(f"Error in objective_system.update: {e}")

                    # Update army system (replaces old spawner and enemy AI)
                    try:
                        self.army_manager.update(dt)
                    except Exception as e:
                        print(f"Error in army_manager.update: {e}")
                        import traceback
                        traceback.print_exc()

                    # Update all systems
                    for system in self.engine.systems:
                        try:
                            system.update(dt)
                        except Exception as e:
                            print(f"Error in system {system.__class__.__name__}.update: {e}")
                            import traceback
                            traceback.print_exc()

                    # Process player attacks - create visual attack entities AND register damage
                    try:
                        for attack in self.player_attack_system.pending_attacks:
                            # Choose color based on attack type
                            if attack['type'] == 'light':
                                color = (255, 255, 100)  # Yellow
                            elif attack['type'] == 'heavy':
                                color = (255, 150, 50)   # Orange
                            elif attack['type'] == 'musou':
                                color = (255, 50, 255)   # Purple/Magenta
                            else:
                                color = (255, 255, 255)

                            # Create visible attack entity
                            create_attack(
                                self.engine.entity_manager,
                                attack['position'][0],
                                attack['position'][1],
                                attack['radius'],
                                attack['damage'],
                                attack['duration'],
                                attack['team'],
                                color
                            )

                            # CRITICAL: Register attack with CombatSystem for damage application
                            self.combat_system.add_attack(
                                attack['position'][0],
                                attack['position'][1],
                                attack['radius'],
                                attack['damage'],
                                attack['team']
                            )
                        self.player_attack_system.pending_attacks.clear()
                    except Exception as e:
                        print(f"Error creating attacks: {e}")
                        import traceback
                        traceback.print_exc()

                    # Update entity components
                    try:
                        self.engine.entity_manager.update(dt)
                    except Exception as e:
                        print(f"Error in entity_manager.update: {e}")

                    # Update particles and popups
                    try:
                        self.particle_system.update(dt)
                        self.popup_system.update(dt)
                    except Exception as e:
                        print(f"Error in particle/popup.update: {e}")

                    # Debug enemy state (optional - enable with F5)
                    if self.debug_enemy_state:
                        enemies = self.engine.entity_manager.get_entities_with_tag("enemy")
                        for e in enemies[:5]:  # Only log first 5 to avoid spam
                            transform = e.get_component("Transform")
                            sprite = e.get_component("Sprite")
                            health = e.get_component("Health")
                            if transform and sprite and health:
                                print(f"Enemy {e.id}: active={e.active}, visible={sprite.visible}, " +
                                      f"pos=({int(transform.x)},{int(transform.y)}), " +
                                      f"hp={int(health.current_health)}/{int(health.max_health)}, dead={health.dead}")

                    # Clean up inactive entities
                    try:
                        self.engine.entity_manager.cleanup()
                    except Exception as e:
                        print(f"Error in entity_manager.cleanup: {e}")

                    # Debug logging after all updates
                    if self.debug_logging:
                        debug_logger.log_enemy_state(
                            self.engine.entity_manager,
                            self.render_system.camera_x,
                            self.render_system.camera_y
                        )

                # Render
                try:
                    self.render()
                except Exception as e:
                    print(f"Error in render: {e}")
                    import traceback
                    traceback.print_exc()

                # Draw overlays
                try:
                    self.controls_overlay.draw()
                except Exception as e:
                    print(f"Error in controls_overlay.draw: {e}")

                # Draw menus
                try:
                    if self.paused:
                        self.pause_menu.draw()

                    if self.keyboard_menu.active:
                        self.keyboard_menu.draw()
                except Exception as e:
                    print(f"Error drawing menus: {e}")

                # Draw debug
                try:
                    if self.engine.show_debug:
                        self.draw_debug()
                        # Draw army debug visualization (command radii, formations)
                        self.army_manager.draw_debug(
                            self.engine.screen,
                            self.render_system.camera_x,
                            self.render_system.camera_y
                        )
                except Exception as e:
                    print(f"Error in draw_debug: {e}")

                pygame.display.flip()

            except Exception as e:
                print(f"CRITICAL ERROR in main loop: {e}")
                import traceback
                traceback.print_exc()
                # Don't exit immediately, let user see the error
                input("Press Enter to exit...")
                break

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.engine.running = False

            # Handle zoom input (mouse wheel and +/- keys)
            elif event.type == pygame.MOUSEWHEEL:
                self.camera_system.handle_zoom_input(event)

            elif event.type == pygame.KEYDOWN:
                # Handle menu events first
                if self.keyboard_menu.active:
                    self.keyboard_menu.handle_event(event)
                    continue

                if self.paused:
                    action = self.pause_menu.handle_event(event)
                    if action == "resume":
                        self.paused = False
                    elif action == "controls":
                        self.keyboard_menu.active = True
                    elif action == "quit":
                        self.engine.running = False
                    continue

                # Zoom controls (+/- keys)
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_MINUS):
                    self.camera_system.handle_zoom_input(event)

                # Normal game controls
                elif event.key == pygame.K_F1:
                    self.controls_overlay.toggle()
                elif event.key == pygame.K_F2:
                    self.keyboard_menu.active = True
                elif event.key == pygame.K_F3:
                    self.engine.show_debug = not self.engine.show_debug
                elif event.key == pygame.K_F4:
                    self.show_flowfield = not self.show_flowfield
                elif event.key == pygame.K_F5:
                    self.debug_enemy_state = not self.debug_enemy_state
                    print(f"Enemy debug logging: {'ON' if self.debug_enemy_state else 'OFF'}")
                elif event.key == pygame.K_F6:
                    self.debug_logging = not self.debug_logging
                    if self.debug_logging:
                        debug_logger.start()
                    else:
                        debug_logger.stop()
                elif event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.engine.running = False

    def render(self):
        """Render game"""
        # Clear screen
        self.engine.screen.fill((30, 30, 40))

        # Draw world grid
        self.draw_world_grid()

        # Draw bases
        self.draw_bases()

        # Draw flow field (debug)
        if self.show_flowfield:
            self.flowfield.draw_debug(
                self.engine.screen,
                (self.render_system.camera_x, self.render_system.camera_y)
            )

        # Draw entities
        self.render_system.update(0)

        # Draw particles and damage popups (after entities, before UI)
        camera_offset = (self.render_system.camera_x, self.render_system.camera_y)
        self.particle_system.draw(self.engine.screen, camera_offset)
        self.popup_system.draw(self.engine.screen, camera_offset)

        # Draw UI
        self.ui_system.update(0)

    def draw_world_grid(self):
        """Draw background grid"""
        grid_size = 200
        camera_x = self.render_system.camera_x
        camera_y = self.render_system.camera_y

        # Vertical lines
        start_x = (camera_x // grid_size) * grid_size
        for x in range(int(start_x), int(camera_x + self.SCREEN_WIDTH + grid_size), grid_size):
            screen_x = x - camera_x
            pygame.draw.line(
                self.engine.screen,
                (40, 40, 50),
                (screen_x, 0),
                (screen_x, self.SCREEN_HEIGHT),
                1
            )

        # Horizontal lines
        start_y = (camera_y // grid_size) * grid_size
        for y in range(int(start_y), int(camera_y + self.SCREEN_HEIGHT + grid_size), grid_size):
            screen_y = y - camera_y
            pygame.draw.line(
                self.engine.screen,
                (40, 40, 50),
                (0, screen_y),
                (self.SCREEN_WIDTH, screen_y),
                1
            )

    def draw_bases(self):
        """Draw capturable bases"""
        camera_x = self.render_system.camera_x
        camera_y = self.render_system.camera_y

        for base in self.objective_system.bases:
            screen_x = base.x - camera_x
            screen_y = base.y - camera_y

            # Draw base circle
            pygame.draw.circle(
                self.engine.screen,
                base.color,
                (int(screen_x), int(screen_y)),
                base.radius,
                3
            )

            # Draw capture progress (bi-directional bar)
            progress_width = 100
            progress_height = 10
            bar_x = screen_x - progress_width // 2
            bar_y = screen_y - base.radius - 20

            # Background
            pygame.draw.rect(
                self.engine.screen,
                (100, 100, 100),
                (bar_x, bar_y, progress_width, progress_height)
            )

            # Bi-directional progress:
            # Left side (RED/Team 1): fills when progress < 0.5
            # Right side (BLUE/Team 0): fills when progress > 0.5
            center_x = bar_x + progress_width // 2

            if base.capture_progress < 0.5:
                # Red (team 1) is capturing - fill from center leftward
                red_progress = (0.5 - base.capture_progress) * 2  # 0.0 to 1.0
                red_width = int((progress_width // 2) * red_progress)
                pygame.draw.rect(
                    self.engine.screen,
                    (255, 100, 100),  # Red
                    (center_x - red_width, bar_y, red_width, progress_height)
                )
            elif base.capture_progress > 0.5:
                # Blue (team 0) is capturing - fill from center rightward
                blue_progress = (base.capture_progress - 0.5) * 2  # 0.0 to 1.0
                blue_width = int((progress_width // 2) * blue_progress)
                pygame.draw.rect(
                    self.engine.screen,
                    (100, 200, 255),  # Blue
                    (center_x, bar_y, blue_width, progress_height)
                )

            # Draw center line to show neutral point
            pygame.draw.line(
                self.engine.screen,
                (255, 255, 255),
                (center_x, bar_y),
                (center_x, bar_y + progress_height),
                1
            )

            # Draw name
            font = pygame.font.Font(None, 20)
            text = font.render(base.name, True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen_x, screen_y - base.radius - 35))
            self.engine.screen.blit(text, text_rect)

    def draw_debug(self):
        """Draw debug information"""
        self.engine.draw_debug_info()

        # Pool stats
        stats = self.pool_manager.get_stats()
        font = pygame.font.Font(None, 20)
        y_offset = self.SCREEN_HEIGHT - 130

        for pool_name, pool_stats in stats.items():
            text = font.render(
                f"{pool_name}: {pool_stats['in_use']}/{pool_stats['total']}",
                True, (100, 255, 100)
            )
            self.engine.screen.blit(text, (10, y_offset))
            y_offset += 20


if __name__ == "__main__":
    game = MusouGame()
    game.run()
