"""
Blackboard system for shared battlefield intelligence
All AI units can read/write to coordinate strategies
"""
import math
from collections import defaultdict


class BattlefieldBlackboard:
    """
    Shared knowledge system for army coordination.
    Generals write strategic goals, Officers write tactical data, Soldiers read orders.
    """
    def __init__(self):
        # Strategic data (written by Generals)
        self.strategic_goals = {}  # team_id -> {"objective": "attack_base", "target": base_obj}

        # Tactical data (written by Officers)
        self.squad_assignments = {}  # squad_id -> {"officer_id": X, "soldier_ids": [], "formation": "line"}
        self.squad_positions = {}  # squad_id -> (x, y)
        self.squad_targets = {}  # squad_id -> entity_id or (x, y)

        # Battlefield intelligence (written by all)
        self.known_enemies = defaultdict(list)  # team_id -> [enemy_positions]
        self.known_threats = defaultdict(list)  # team_id -> [(x, y, threat_level)]
        self.base_status = {}  # base_name -> {"owner": team_id, "threat_level": float}

        # Morale and cohesion
        self.team_morale = {0: 1.0, 1: 1.0}  # 0.0 = broken, 1.0 = high morale
        self.squad_cohesion = {}  # squad_id -> float (0-1, how tight formation is)

        # Scout system
        self.squad_scouts = {}  # squad_id -> [soldier_ids] of scouts
        self.scout_positions = {}  # scout_id -> (patrol_x, patrol_y) patrol position
        self.scout_reports = []  # [(scout_id, enemy_pos, game_time, enemy_type)]

        # Command system (delays and signal radius)
        self.pending_orders = []  # [(order_time, recipient_id, order_data)]
        self.command_delays = {
            "general_to_officer": 0.5,  # 0.5s delay
            "officer_to_soldier": 0.2,  # 0.2s delay
        }

        # Statistics
        self.team_stats = {
            0: {"total_units": 0, "soldiers": 0, "officers": 0, "generals": 0, "casualties": 0},
            1: {"total_units": 0, "soldiers": 0, "officers": 0, "generals": 0, "casualties": 0}
        }

    def set_strategic_goal(self, team_id, objective_type, target_data):
        """General sets strategic goal for entire team"""
        self.strategic_goals[team_id] = {
            "objective": objective_type,  # "attack_base", "defend_base", "advance", "retreat"
            "target": target_data,
            "priority": 1.0
        }

    def get_strategic_goal(self, team_id):
        """Get current strategic goal for team"""
        return self.strategic_goals.get(team_id, None)

    def register_squad(self, squad_id, officer_id, formation="line"):
        """Officer registers their squad"""
        self.squad_assignments[squad_id] = {
            "officer_id": officer_id,
            "soldier_ids": [],
            "formation": formation,
            "max_size": 10
        }
        self.squad_cohesion[squad_id] = 1.0

    def add_soldier_to_squad(self, squad_id, soldier_id):
        """Add soldier to squad"""
        if squad_id in self.squad_assignments:
            squad = self.squad_assignments[squad_id]
            if len(squad["soldier_ids"]) < squad["max_size"]:
                squad["soldier_ids"].append(soldier_id)
                return True
        return False

    def remove_soldier_from_squad(self, squad_id, soldier_id):
        """Remove soldier from squad (death or reassignment)"""
        if squad_id in self.squad_assignments:
            squad = self.squad_assignments[squad_id]
            if soldier_id in squad["soldier_ids"]:
                squad["soldier_ids"].remove(soldier_id)

    def get_squad_info(self, squad_id):
        """Get squad information"""
        return self.squad_assignments.get(squad_id, None)

    def get_soldier_squad(self, soldier_id):
        """Find which squad a soldier belongs to"""
        for squad_id, squad_data in self.squad_assignments.items():
            if soldier_id in squad_data["soldier_ids"]:
                return squad_id
        return None

    def update_squad_position(self, squad_id, x, y):
        """Officer updates squad position"""
        self.squad_positions[squad_id] = (x, y)

    def get_squad_position(self, squad_id):
        """Get squad's current position"""
        return self.squad_positions.get(squad_id, (0, 0))

    def set_squad_target(self, squad_id, target):
        """Officer sets squad target (entity or position)"""
        self.squad_targets[squad_id] = target

    def get_squad_target(self, squad_id):
        """Get squad's current target"""
        return self.squad_targets.get(squad_id, None)

    def report_enemy_sighting(self, team_id, enemy_pos, enemy_type="soldier"):
        """Unit reports enemy sighting"""
        self.known_enemies[team_id].append({
            "position": enemy_pos,
            "type": enemy_type,
            "last_seen": 0  # Will be updated with game time
        })

    def update_morale(self, team_id, delta):
        """Adjust team morale"""
        self.team_morale[team_id] = max(0.0, min(1.0, self.team_morale[team_id] + delta))

    def get_morale(self, team_id):
        """Get team morale (0-1)"""
        return self.team_morale.get(team_id, 0.5)

    def update_cohesion(self, squad_id, cohesion_value):
        """Update squad cohesion (how tight formation is)"""
        self.squad_cohesion[squad_id] = max(0.0, min(1.0, cohesion_value))

    def get_cohesion(self, squad_id):
        """Get squad cohesion"""
        return self.squad_cohesion.get(squad_id, 1.0)

    def issue_order(self, recipient_id, order_data, command_type="officer_to_soldier", current_time=0):
        """Issue order with realistic delay"""
        delay = self.command_delays.get(command_type, 0.1)
        delivery_time = current_time + delay
        self.pending_orders.append((delivery_time, recipient_id, order_data))

    def get_orders_for_unit(self, unit_id, current_time):
        """Get any orders ready for this unit"""
        ready_orders = []
        remaining_orders = []

        for order_time, recipient_id, order_data in self.pending_orders:
            if recipient_id == unit_id and order_time <= current_time:
                ready_orders.append(order_data)
            else:
                remaining_orders.append((order_time, recipient_id, order_data))

        self.pending_orders = remaining_orders
        return ready_orders

    def update_team_stats(self, team_id, entity_manager):
        """Update team statistics from entity manager"""
        stats = {"total_units": 0, "soldiers": 0, "officers": 0, "generals": 0, "casualties": 0}

        team_tag = f"team_{team_id}"
        units = entity_manager.get_entities_with_tag(team_tag)

        for unit in units:
            if not unit.active:
                continue

            health = unit.get_component("Health")
            if health and health.dead:
                stats["casualties"] += 1
                continue

            stats["total_units"] += 1

            if unit.has_tag("soldier"):
                stats["soldiers"] += 1
            elif unit.has_tag("officer"):
                stats["officers"] += 1
            elif unit.has_tag("general"):
                stats["generals"] += 1

        self.team_stats[team_id] = stats

    def get_team_stats(self, team_id):
        """Get team statistics"""
        return self.team_stats.get(team_id, {})

    def calculate_local_superiority(self, team_id, x, y, radius, entity_manager):
        """Calculate if team has local superiority at position (power-based, not count-based)"""
        team_tag = f"team_{team_id}"
        enemy_team = 1 - team_id  # Simple 2-team system
        enemy_tag = f"team_{enemy_team}"

        RANK_COMBAT_POWER = {
            "soldier": 1.0,
            "officer": 2.0,
            "general": 3.0
        }

        friendly_power = 0.0
        enemy_power = 0.0

        # Count friendly units with rank weighting
        for unit_entity in entity_manager.get_entities_with_tag(team_tag):
            if not unit_entity.active:
                continue

            health = unit_entity.get_component("Health")
            if health and health.dead:
                continue

            transform = unit_entity.get_component("Transform")
            if transform:
                dx = transform.x - x
                dy = transform.y - y
                if math.sqrt(dx*dx + dy*dy) <= radius:
                    unit = unit_entity.get_component("Unit")
                    power = RANK_COMBAT_POWER.get(unit.rank, 1.0) if unit else 1.0
                    friendly_power += power

        # Count enemy units with rank weighting
        for unit_entity in entity_manager.get_entities_with_tag(enemy_tag):
            if not unit_entity.active:
                continue

            health = unit_entity.get_component("Health")
            if health and health.dead:
                continue

            transform = unit_entity.get_component("Transform")
            if transform:
                dx = transform.x - x
                dy = transform.y - y
                if math.sqrt(dx*dx + dy*dy) <= radius:
                    unit = unit_entity.get_component("Unit")
                    power = RANK_COMBAT_POWER.get(unit.rank, 1.0) if unit else 1.0
                    enemy_power += power

        total_power = friendly_power + enemy_power
        if total_power == 0:
            return 0.5

        return friendly_power / total_power

    def calculate_threat_level(self, team_id, x, y, radius, entity_manager):
        """
        Calculate threat level at location.
        Returns: "low", "medium", "high", "overwhelming"
        """
        superiority = self.calculate_local_superiority(team_id, x, y, radius, entity_manager)

        # Convert superiority to threat level
        if superiority >= 0.7:
            return "low"  # We dominate
        elif superiority >= 0.5:
            return "medium"  # Even fight
        elif superiority >= 0.3:
            return "high"  # Enemy has advantage
        else:
            return "overwhelming"  # Enemy dominates

    def assign_scouts(self, squad_id, scout_ids, patrol_positions):
        """Assign scouts to a squad with patrol positions"""
        self.squad_scouts[squad_id] = scout_ids
        for i, scout_id in enumerate(scout_ids):
            if i < len(patrol_positions):
                self.scout_positions[scout_id] = patrol_positions[i]

    def get_scouts_for_squad(self, squad_id):
        """Get list of scout soldier IDs for a squad"""
        return self.squad_scouts.get(squad_id, [])

    def is_scout(self, soldier_id):
        """Check if a soldier is assigned as scout"""
        for squad_id, scouts in self.squad_scouts.items():
            if soldier_id in scouts:
                return True
        return False

    def get_scout_patrol_position(self, soldier_id):
        """Get patrol position for a scout"""
        return self.scout_positions.get(soldier_id, None)

    def report_scout_sighting(self, scout_id, enemy_pos, game_time, enemy_type="unknown"):
        """Scout reports enemy sighting"""
        self.scout_reports.append((scout_id, enemy_pos, game_time, enemy_type))
        print(f"[SCOUT {scout_id}] Enemy {enemy_type} spotted at ({int(enemy_pos[0])}, {int(enemy_pos[1])})")

    def recall_scouts(self, squad_id):
        """Recall all scouts for a squad"""
        if squad_id in self.squad_scouts:
            scouts = self.squad_scouts[squad_id]
            for scout_id in scouts:
                if scout_id in self.scout_positions:
                    del self.scout_positions[scout_id]
            self.squad_scouts[squad_id] = []
