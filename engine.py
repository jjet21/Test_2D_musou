"""
Core game engine with systems loop
"""
import pygame
from core.entity import EntityManager


class System:
    """Base system class"""
    def __init__(self, entity_manager):
        self.entity_manager = entity_manager

    def update(self, dt):
        """Override in subclasses"""
        pass


class GameEngine:
    """Main game engine"""
    def __init__(self, width=1280, height=720, title="2D Musou Game"):
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60

        # Entity-Component System
        self.entity_manager = EntityManager()

        # Systems list (will be populated by game)
        self.systems = []

        # Debug info
        self.show_debug = False
        self.frame_times = []
        self.max_frame_samples = 60

    def add_system(self, system):
        """Add a system to the engine"""
        self.systems.append(system)

    def run(self):
        """Main game loop"""
        self.running = True

        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0  # Delta time in seconds

            # Track frame time for debug
            if self.show_debug:
                self.frame_times.append(dt)
                if len(self.frame_times) > self.max_frame_samples:
                    self.frame_times.pop(0)

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        self.show_debug = not self.show_debug

            # Update all systems
            for system in self.systems:
                system.update(dt)

            # Update entity components
            self.entity_manager.update(dt)

            # Clean up inactive entities
            self.entity_manager.cleanup()

            # Draw debug info if enabled
            if self.show_debug:
                self.draw_debug_info()

            pygame.display.flip()

        pygame.quit()

    def draw_debug_info(self):
        """Draw debug overlay"""
        font = pygame.font.Font(None, 24)

        # FPS
        fps_text = font.render(f"FPS: {int(self.clock.get_fps())}", True, (0, 255, 0))
        self.screen.blit(fps_text, (10, self.height - 80))

        # Entity count
        entity_count = len([e for e in self.entity_manager.entities if e.active])
        entity_text = font.render(f"Entities: {entity_count}", True, (0, 255, 0))
        self.screen.blit(entity_text, (10, self.height - 55))

        # Average frame time
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            frame_text = font.render(f"Frame: {avg_frame_time*1000:.1f}ms", True, (0, 255, 0))
            self.screen.blit(frame_text, (10, self.height - 30))

    def stop(self):
        """Stop the engine"""
        self.running = False
