"""
Capturable bases and objective system
"""
import json
import math


class Base:
    """Capturable base on the battlefield"""
    def __init__(self, name, x, y, radius=100):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius

        # Ownership (-1 = neutral, 0 = team 0/blue, 1 = team 1/red)
        self.owner = -1
        self.capture_progress = 0.5  # 0 = full team 1, 1 = full team 0
        self.capture_rate = 0.2  # Per second per unit

        # Visual
        self.color = self.get_color()

    def get_color(self):
        """Get color based on ownership"""
        if self.capture_progress < 0.4:
            return (255, 100, 100)  # Enemy red
        elif self.capture_progress > 0.6:
            return (100, 200, 255)  # Player blue
        else:
            return (200, 200, 200)  # Neutral gray

    def update(self, dt, team0_power, team1_power):
        """Update capture progress based on team power"""
        # Calculate capture influence (power-based, not count-based)
        net_influence = (team0_power - team1_power) * self.capture_rate * dt

        # Apply to progress
        self.capture_progress += net_influence
        self.capture_progress = max(0.0, min(1.0, self.capture_progress))

        # Debug output when units are capturing
        if team0_power > 0 or team1_power > 0:
            print(f"[CAPTURE] {self.name}: Team0={team0_power:.1f} vs Team1={team1_power:.1f}, Progress={self.capture_progress:.2f}")

        # Update ownership (now correctly mapped to team IDs)
        old_owner = self.owner
        if self.capture_progress < 0.3:
            self.owner = 1  # Team 1 (red/enemy)
        elif self.capture_progress > 0.7:
            self.owner = 0  # Team 0 (blue/player)
        else:
            self.owner = -1  # Neutral

        # Update color
        self.color = self.get_color()

        # Return True if ownership changed
        return old_owner != self.owner

    def is_unit_in_range(self, x, y):
        """Check if a unit is in capture range"""
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance <= self.radius


class ObjectiveSystem:
    """Manages battlefield objectives and bases"""
    def __init__(self, entity_manager, flowfield):
        self.entity_manager = entity_manager
        self.flowfield = flowfield
        self.bases = []
        self.player_score = 0
        self.enemy_score = 0

    def load_config(self, config_path):
        """Load objectives from JSON"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                bases_data = data.get('bases', [])

                for base_data in bases_data:
                    base = Base(
                        base_data['name'],
                        base_data['x'],
                        base_data['y'],
                        base_data.get('radius', 100)
                    )
                    self.bases.append(base)
                return True
        except Exception as e:
            print(f"Failed to load objective config: {e}")
            return False

    def add_base(self, name, x, y, radius=100):
        """Manually add a base"""
        base = Base(name, x, y, radius)
        self.bases.append(base)
        return base

    def update(self, dt):
        """Update all bases"""
        try:
            # Get all active army units (soldiers, officers, generals)
            all_units = self.entity_manager.get_entities_with_tag("unit")

            # Also include player
            player_entities = self.entity_manager.get_entities_with_tag("player")

            for base in self.bases:
                # Calculate capture power (not just count) for each team
                team0_power = 0.0  # Blue/Player team
                team1_power = 0.0  # Red/Enemy team

                # Rank-based capture rates
                RANK_CAPTURE_RATES = {
                    "soldier": 0.1,
                    "officer": 0.3,
                    "general": 0.5
                }

                # Count army units by team with rank multipliers
                for unit_entity in all_units:
                    if not unit_entity.active:
                        continue

                    # Skip dead units
                    health = unit_entity.get_component("Health")
                    if health and health.dead:
                        continue

                    transform = unit_entity.get_component("Transform")
                    unit = unit_entity.get_component("Unit")

                    if transform and unit and base.is_unit_in_range(transform.x, transform.y):
                        # Get rank-based capture rate
                        capture_rate = RANK_CAPTURE_RATES.get(unit.rank, 0.1)

                        if unit.team == 0:
                            team0_power += capture_rate
                        elif unit.team == 1:
                            team1_power += capture_rate

                # Count player (if not already an army unit)
                for player in player_entities:
                    if player.active:
                        health = player.get_component("Health")
                        if health and health.dead:
                            continue
                        transform = player.get_component("Transform")
                        if transform and base.is_unit_in_range(transform.x, transform.y):
                            # Player captures at soldier rate
                            team0_power += 0.1

                # Update base with capture power (not count)
                ownership_changed = base.update(dt, team0_power, team1_power)

                if ownership_changed:
                    self.on_base_captured(base)

            # Update flow field targets based on player-owned bases
            self.update_flowfield_targets()
        except Exception as e:
            print(f"Error in ObjectiveSystem.update: {e}")

    def on_base_captured(self, base):
        """Handle base capture event"""
        owner_names = {-1: 'Neutral', 0: 'Team 0 (Blue)', 1: 'Team 1 (Red)'}
        print(f"Base '{base.name}' captured by {owner_names.get(base.owner, 'Unknown')}!")

        # Update score
        if base.owner == 0:
            self.player_score += 100
        elif base.owner == 1:
            self.enemy_score += 100

    def update_flowfield_targets(self):
        """Update flow field to target player-owned bases"""
        self.flowfield.clear_targets()

        # Add player-owned bases as targets (team 0)
        for base in self.bases:
            if base.owner == 0:
                self.flowfield.add_target(base.x, base.y)

        # If no player bases, target player position
        if not self.flowfield.targets:
            players = self.entity_manager.get_entities_with_tag("player")
            if players:
                player_transform = players[0].get_component("Transform")
                if player_transform:
                    self.flowfield.add_target(player_transform.x, player_transform.y)

    def get_player_bases(self):
        """Get list of player-owned bases (team 0)"""
        return [b for b in self.bases if b.owner == 0]

    def get_enemy_bases(self):
        """Get list of enemy-owned bases (team 1)"""
        return [b for b in self.bases if b.owner == 1]

    def get_neutral_bases(self):
        """Get list of neutral bases"""
        return [b for b in self.bases if b.owner == -1]
