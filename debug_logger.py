"""
Debug logger for tracking enemy state frame-by-frame
"""
import time
from datetime import datetime


class DebugLogger:
    """Logs entity state to file for debugging"""
    def __init__(self, filename="debug_log.txt"):
        self.filename = filename
        self.frame = 0
        self.enabled = False
        self.file = None

    def start(self):
        """Start logging"""
        self.enabled = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"debug_log_{timestamp}.txt"
        self.file = open(self.filename, 'w')
        self.file.write(f"=== DEBUG LOG STARTED {timestamp} ===\n\n")
        self.file.flush()
        print(f"[DEBUG] Logging to {self.filename}")

    def stop(self):
        """Stop logging"""
        if self.file:
            self.file.write(f"\n=== DEBUG LOG ENDED (Frame {self.frame}) ===\n")
            self.file.close()
            self.file = None
        self.enabled = False
        print(f"[DEBUG] Log saved to {self.filename}")

    def log_frame_start(self):
        """Mark start of new frame"""
        if not self.enabled or not self.file:
            return
        self.frame += 1
        self.file.write(f"\n{'='*60}\n")
        self.file.write(f"FRAME {self.frame}\n")
        self.file.write(f"{'='*60}\n")

    def log_enemy_state(self, entity_manager, camera_x=0, camera_y=0):
        """Log all enemy states"""
        if not self.enabled or not self.file:
            return

        enemies = entity_manager.get_entities_with_tag("enemy")
        self.file.write(f"\nTotal enemies in manager: {len(enemies)}\n")
        self.file.write(f"Camera position: ({camera_x:.1f}, {camera_y:.1f})\n\n")

        active_count = 0
        visible_count = 0
        dead_count = 0

        for enemy in enemies:
            transform = enemy.get_component("Transform")
            health = enemy.get_component("Health")
            sprite = enemy.get_component("Sprite")
            ai = enemy.get_component("AI")

            if enemy.active:
                active_count += 1
            if health and health.dead:
                dead_count += 1
            if sprite and sprite.visible and enemy.active and (not health or not health.dead):
                visible_count += 1

            # Log detailed state for active or recently dead enemies
            if enemy.active or (health and health.dead):
                tags = ", ".join(enemy.tags)
                self.file.write(f"Enemy ID={enemy.id} [{tags}]\n")
                self.file.write(f"  active={enemy.active}\n")

                if transform:
                    screen_x = transform.x - camera_x
                    screen_y = transform.y - camera_y
                    self.file.write(f"  pos=({transform.x:.1f}, {transform.y:.1f}) screen=({screen_x:.1f}, {screen_y:.1f})\n")
                    self.file.write(f"  vel=({transform.vx:.1f}, {transform.vy:.1f})\n")
                else:
                    self.file.write(f"  pos=NO_TRANSFORM\n")

                if health:
                    self.file.write(f"  health={health.current_health:.1f}/{health.max_health} dead={health.dead} invuln={health.invulnerable}\n")
                else:
                    self.file.write(f"  health=NO_HEALTH_COMPONENT\n")

                if sprite:
                    self.file.write(f"  sprite.visible={sprite.visible} layer={sprite.layer}\n")
                else:
                    self.file.write(f"  sprite=NO_SPRITE_COMPONENT\n")

                if ai:
                    self.file.write(f"  ai.state={ai.state}\n")

                self.file.write("\n")

        self.file.write(f"Summary: {active_count} active, {visible_count} should render, {dead_count} dead\n")
        self.file.flush()

    def log_event(self, message):
        """Log a custom event"""
        if not self.enabled or not self.file:
            return
        self.file.write(f"[EVENT] {message}\n")
        self.file.flush()

    def log_player_state(self, entity_manager):
        """Log player state"""
        if not self.enabled or not self.file:
            return

        players = entity_manager.get_entities_with_tag("player")
        if players:
            player = players[0]
            transform = player.get_component("Transform")
            if transform:
                self.file.write(f"\nPlayer pos=({transform.x:.1f}, {transform.y:.1f})\n")
                self.file.flush()


# Global instance
debug_logger = DebugLogger()
