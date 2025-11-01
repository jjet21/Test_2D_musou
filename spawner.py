"""
JSON-driven enemy spawner system
"""
import json
import random


class Spawner:
    """Spawns enemies based on JSON configuration"""
    def __init__(self, entity_manager, pool_manager):
        self.entity_manager = entity_manager
        self.pool_manager = pool_manager
        self.spawn_points = []
        self.spawn_configs = {}
        self.active = True

    def load_config(self, config_path):
        """Load spawner configuration from JSON"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                self.spawn_configs = data.get('spawners', {})
                return True
        except Exception as e:
            print(f"Failed to load spawner config: {e}")
            return False

    def add_spawn_point(self, name, x, y, enemy_type="grunt", rate=2.0, max_enemies=50):
        """Add a spawn point"""
        self.spawn_points.append({
            'name': name,
            'x': x,
            'y': y,
            'enemy_type': enemy_type,
            'rate': rate,  # Enemies per second
            'max': max_enemies,
            'timer': 0,
            'spawned_count': 0,
            'min_spawn_interval': 0.5  # Minimum 0.5s between spawns at this point
        })

    def update(self, dt):
        """Update all spawn points"""
        if not self.active:
            return

        for spawn_point in self.spawn_points:
            spawn_point['timer'] += dt

            # Check if it's time to spawn (respect both rate and minimum interval)
            interval = max(1.0 / max(spawn_point['rate'], 0.0001), spawn_point['min_spawn_interval'])
            if spawn_point['timer'] >= interval:
                spawn_point['timer'] -= interval  # Preserve leftover time

                # Count active enemies from this spawn point's type
                active_count = self._count_active_enemies(spawn_point['enemy_type'])

                # Check spawn limit based on active enemies, not total spawned
                if active_count < spawn_point['max']:
                    enemy = self.spawn_enemy(spawn_point)
                    spawn_point['spawned_count'] += 1

    def spawn_enemy(self, spawn_point):
        """Spawn an enemy at a spawn point"""
        # Add randomness to spawn position to avoid spawn camping
        # Clamp to ensure spawns stay within world bounds (assuming 3200x2400 world)
        x = max(50, min(3150, spawn_point['x'] + random.uniform(-100, 100)))
        y = max(50, min(2350, spawn_point['y'] + random.uniform(-100, 100)))

        enemy_type = spawn_point['enemy_type']

        # Try to get from pool
        if self.pool_manager:
            pool_name = f"enemy_{enemy_type}"
            enemy = self.pool_manager.acquire(pool_name)
            if enemy:
                # Reset Transform completely
                transform = enemy.get_component("Transform")
                if transform:
                    transform.x = x
                    transform.y = y
                    transform.vx = 0
                    transform.vy = 0
                    transform.rotation = 0

                # Reset Health
                health = enemy.get_component("Health")
                if health:
                    health.current_health = health.max_health
                    health.dead = False

                # Reset AI state
                ai = enemy.get_component("AI")
                if ai and hasattr(ai, 'reset'):
                    ai.reset()

                # Reset Sprite
                sprite = enemy.get_component("Sprite")
                if sprite:
                    if hasattr(sprite, 'reset'):
                        sprite.reset()
                    sprite.visible = True

                # Ensure entity is active
                if not enemy.active:
                    enemy.active = True

                return enemy

        # Fallback: create new enemy (if pool is not available)
        from game.enemy import create_grunt, create_officer
        if enemy_type == "grunt":
            return create_grunt(self.entity_manager, x, y)
        elif enemy_type == "officer":
            return create_officer(self.entity_manager, x, y)

    def reset_spawn_point(self, name):
        """Reset a spawn point's counter"""
        for spawn_point in self.spawn_points:
            if spawn_point['name'] == name:
                spawn_point['spawned_count'] = 0
                spawn_point['timer'] = 0

    def clear_spawn_points(self):
        """Clear all spawn points"""
        self.spawn_points.clear()

    def _count_active_enemies(self, enemy_type):
        """Count active AND alive enemies of a specific type"""
        count = 0
        tag = enemy_type  # "grunt" or "officer"
        enemies = self.entity_manager.get_entities_with_tag(tag)
        for enemy in enemies:
            if enemy.active:
                # Also check if enemy is actually alive (not dead)
                health = enemy.get_component("Health")
                if health and not health.dead:
                    count += 1
        return count
