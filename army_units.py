"""
Army unit hierarchy with rank progression support
Soldiers -> Officers -> Generals
Player starts as soldier, can eventually promote
"""
import pygame
import math
from core.entity import Entity
from core.component import Transform, Sprite, Health, Combat, AI


class UnitRank:
    """Unit rank constants"""
    SOLDIER = "soldier"
    OFFICER = "officer"
    GENERAL = "general"


class UnitComponent:
    """
    Component to track unit rank and command relationships.
    Supports player rank progression.
    """
    def __init__(self, rank=UnitRank.SOLDIER, team=0):
        self.rank = rank
        self.team = team
        self.squad_id = None  # Assigned squad
        self.commander_id = None  # ID of commanding officer/general
        self.subordinates = []  # IDs of units under command

        # Morale and performance
        self.morale = 1.0  # 0-1, affects combat effectiveness
        self.experience = 0  # For potential promotions

        # Formation tracking
        self.formation_position = None  # Ideal (x, y) in formation
        self.formation_deviation = 0.0  # Distance from ideal position

    def promote_to(self, new_rank):
        """Promote unit to higher rank (for player progression)"""
        if new_rank in [UnitRank.SOLDIER, UnitRank.OFFICER, UnitRank.GENERAL]:
            old_rank = self.rank
            self.rank = new_rank
            return old_rank
        return None

    def can_command(self):
        """Check if unit can command others"""
        return self.rank in [UnitRank.OFFICER, UnitRank.GENERAL]

    def update_morale(self, delta):
        """Adjust morale"""
        self.morale = max(0.0, min(1.0, self.morale + delta))

    def get_combat_modifier(self):
        """Get combat effectiveness modifier based on morale"""
        return 0.5 + (self.morale * 0.5)  # 0.5x to 1.0x damage multiplier


def create_soldier(entity_manager, x, y, team=0):
    """Create a soldier unit"""
    entity = entity_manager.create_entity()
    entity.add_tag(f"team_{team}")
    entity.add_tag("soldier")
    entity.add_tag("unit")

    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Soldier sprite (small, team-colored)
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    color = (100, 150, 255) if team == 0 else (255, 100, 100)  # Blue for player, Red for enemy
    pygame.draw.circle(surface, color, (16, 16), 14)
    pygame.draw.circle(surface, (0, 0, 0), (16, 16), 14, 2)
    sprite = Sprite(surface, 32, 32)
    sprite.layer = 5
    entity.add_component("Sprite", sprite)

    health = Health(50)  # Low HP
    entity.add_component("Health", health)

    combat = Combat(damage=10, attack_range=30, attack_cooldown=1.0)
    combat.team = team
    entity.add_component("Combat", combat)

    # Basic AI
    ai = AI("follow_officer")
    entity.add_component("AI", ai)

    # Unit component
    unit = UnitComponent(UnitRank.SOLDIER, team)
    entity.add_component("Unit", unit)

    return entity


def create_officer(entity_manager, x, y, team=0):
    """Create an officer unit"""
    entity = entity_manager.create_entity()
    entity.add_tag(f"team_{team}")
    entity.add_tag("officer")
    entity.add_tag("unit")

    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # Officer sprite (medium, team-colored with gold/silver trim)
    surface = pygame.Surface((48, 48), pygame.SRCALPHA)
    color = (80, 120, 255) if team == 0 else (255, 80, 80)
    trim_color = (255, 215, 0) if team == 0 else (192, 192, 192)  # Gold for player, Silver for enemy

    # Main body
    pygame.draw.circle(surface, color, (24, 24), 20)
    pygame.draw.circle(surface, (0, 0, 0), (24, 24), 20, 3)

    # Trim ring
    pygame.draw.circle(surface, trim_color, (24, 24), 16, 3)

    # Command insignia (chevrons)
    pygame.draw.polygon(surface, trim_color, [(24, 10), (18, 18), (30, 18)])

    sprite = Sprite(surface, 48, 48)
    sprite.layer = 6  # Above soldiers
    entity.add_component("Sprite", sprite)

    health = Health(150)  # Medium HP
    entity.add_component("Health", health)

    combat = Combat(damage=20, attack_range=40, attack_cooldown=0.8)
    combat.team = team
    entity.add_component("Combat", combat)

    # Officer AI
    ai = AI("command_squad")
    entity.add_component("AI", ai)

    # Unit component
    unit = UnitComponent(UnitRank.OFFICER, team)
    entity.add_component("Unit", unit)

    return entity


def create_general(entity_manager, x, y, team=0):
    """Create a general unit"""
    entity = entity_manager.create_entity()
    entity.add_tag(f"team_{team}")
    entity.add_tag("general")
    entity.add_tag("unit")

    transform = Transform(x, y)
    entity.add_component("Transform", transform)

    # General sprite (large, team-colored with crown)
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    color = (60, 100, 255) if team == 0 else (255, 60, 60)
    crown_color = (255, 215, 0)  # Gold crown for both

    # Main body
    pygame.draw.circle(surface, color, (32, 32), 28)
    pygame.draw.circle(surface, (0, 0, 0), (32, 32), 28, 4)

    # Crown
    crown_points = [(20, 14), (26, 8), (32, 4), (38, 8), (44, 14), (40, 20), (32, 18), (24, 20)]
    pygame.draw.polygon(surface, crown_color, crown_points)
    pygame.draw.polygon(surface, (0, 0, 0), crown_points, 2)

    # Command star
    pygame.draw.polygon(surface, (255, 255, 255),
                       [(32, 28), (34, 34), (40, 34), (35, 38), (37, 44), (32, 40), (27, 44), (29, 38), (24, 34), (30, 34)])

    sprite = Sprite(surface, 64, 64)
    sprite.layer = 7  # Above officers
    entity.add_component("Sprite", sprite)

    health = Health(300)  # High HP
    entity.add_component("Health", health)

    combat = Combat(damage=40, attack_range=50, attack_cooldown=0.6)
    combat.team = team
    entity.add_component("Combat", combat)

    # General AI
    ai = AI("command_army")
    entity.add_component("AI", ai)

    # Unit component
    unit = UnitComponent(UnitRank.GENERAL, team)
    entity.add_component("Unit", unit)

    return entity


class OfficerData:
    """
    Additional data for officers managing squads.
    Tracks threat evaluation and reinforcement requests.
    """
    def __init__(self, squad_id):
        self.squad_id = squad_id
        self.local_threat_level = 0.0  # 0-1, higher = more dangerous
        self.retreat_threshold = 1.5  # Retreat if enemies > allies * this
        self.morale_threshold = 0.3  # Retreat if squad morale < this
        self.reinforcement_requested = False
        self.reinforcement_threshold = 0.4  # Request help if squad < 40% strength

    def evaluate_local_threat(self, entity_manager, blackboard, transform, radius=400):
        """
        Evaluate local threat density.
        Returns threat_ratio (enemies / allies).
        """
        unit = self.entity.get_component("Unit")
        if not unit:
            return 0.0

        superiority = blackboard.calculate_local_superiority(
            unit.team, transform.x, transform.y, radius, entity_manager
        )

        # Convert superiority (0-1) to threat ratio
        if superiority > 0.5:
            # We have advantage
            threat_ratio = (1.0 - superiority) / superiority
        else:
            # Enemy has advantage
            threat_ratio = superiority / (1.0 - superiority) if superiority < 1.0 else 999.0

        self.local_threat_level = min(1.0, threat_ratio / 3.0)  # Normalize to 0-1

        return threat_ratio

    def should_retreat(self, threat_ratio, squad_morale):
        """Check if officer should order retreat"""
        return (threat_ratio > self.retreat_threshold or
                squad_morale < self.morale_threshold)

    def check_reinforcement_needed(self, current_strength, max_strength):
        """Check if officer should request reinforcements"""
        strength_ratio = current_strength / max_strength if max_strength > 0 else 0
        return strength_ratio < self.reinforcement_threshold


class GeneralData:
    """
    Additional data for generals managing armies.
    Handles reserves and strategic decision making.
    """
    def __init__(self, team_id):
        self.team_id = team_id
        self.reserve_squads = []  # List of squad_ids held in reserve
        self.active_squads = []  # List of squad_ids in combat
        self.reserve_threshold = 0.3  # Keep 30% of force in reserve

        # Strategic triggers
        self.commit_reserves_triggers = {
            "base_lost": False,
            "numerical_inferiority": False,
            "critical_objective": False
        }

    def allocate_reserves(self, total_squads):
        """Determine how many squads to keep in reserve"""
        reserve_count = max(1, int(total_squads * self.reserve_threshold))
        return reserve_count

    def should_commit_reserves(self, blackboard):
        """Check if conditions warrant committing reserves"""
        # Check triggers
        team_stats = blackboard.get_team_stats(self.team_id)
        enemy_stats = blackboard.get_team_stats(1 - self.team_id)

        # Numerical inferiority
        if team_stats["total_units"] < enemy_stats["total_units"] * 0.8:
            self.commit_reserves_triggers["numerical_inferiority"] = True

        # Any trigger active?
        return any(self.commit_reserves_triggers.values())

    def commit_reserve_squad(self):
        """Move one squad from reserve to active"""
        if self.reserve_squads:
            squad_id = self.reserve_squads.pop(0)
            self.active_squads.append(squad_id)
            return squad_id
        return None

    def return_squad_to_reserve(self, squad_id):
        """Return squad to reserves"""
        if squad_id in self.active_squads:
            self.active_squads.remove(squad_id)
            self.reserve_squads.append(squad_id)
