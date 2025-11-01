"""
Formation system with dynamic looseness and command influence radius
"""
import math
import random


class FormationType:
    """Formation types with different characteristics"""
    LINE = "line"          # Defensive, wide front
    COLUMN = "column"      # Marching, narrow front
    WEDGE = "wedge"        # Assault, concentrated tip
    SKIRMISH = "skirmish"  # Loose, irregular
    PROTECTIVE_CIRCLE = "protective_circle"  # Soldiers form circle around officer
    GENERAL_BOX = "general_box"  # Rectangle formation for general's army
    CAPTURE_SPREAD = "capture_spread"  # Spread evenly in circle for base capture


class Formation:
    """
    Formation manager with looseness parameter.
    Looseness: 0 = rigid parade formation, 1 = loose skirmish formation
    """
    def __init__(self, formation_type=FormationType.LINE, looseness=0.3):
        self.type = formation_type
        self.looseness = looseness  # 0-1, affects spacing variance
        self.base_spacing = 50      # Base distance between units
        self.is_broken = False      # Formation integrity
        self.break_threshold = 0.3  # Cohesion below this = broken

    def get_position_in_formation(self, index, total_units, center_x, center_y, facing_angle=0):
        """
        Calculate position for unit at index in formation.
        Returns (x, y) with looseness variance applied.
        """
        # Base spacing with looseness
        spacing = self.base_spacing * (1.0 + self.looseness)

        if self.type == FormationType.LINE:
            # Horizontal line
            offset_x = (index - total_units / 2) * spacing
            offset_y = 0

        elif self.type == FormationType.COLUMN:
            # Vertical column (2-wide)
            column_index = index // 2
            row = index % 2
            offset_x = (row - 0.5) * spacing * 0.5
            offset_y = column_index * spacing

        elif self.type == FormationType.WEDGE:
            # V-shaped wedge
            row = 0
            units_in_row = 1
            temp_index = index

            # Find which row
            while temp_index >= units_in_row:
                temp_index -= units_in_row
                row += 1
                units_in_row += 2  # Each row has 2 more units than previous

            # Position in row
            offset_x = (temp_index - units_in_row / 2) * spacing
            offset_y = row * spacing * 0.866  # sqrt(3)/2 for equilateral triangle

        elif self.type == FormationType.SKIRMISH:
            # Irregular cloud formation
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, total_units * spacing * 0.3)
            offset_x = math.cos(angle) * radius
            offset_y = math.sin(angle) * radius

        elif self.type == FormationType.PROTECTIVE_CIRCLE:
            # Soldiers form concentric circles around center (officer at center)
            # Officer is at index 0 (center), soldiers form rings around
            if index == 0:
                # Officer/leader at center
                offset_x = 0
                offset_y = 0
            else:
                # Soldiers in circles
                soldiers_index = index - 1
                # Determine which ring (0, 1, 2, ...)
                units_per_ring = 6  # First ring has 6, second has 12, etc.
                current_ring = 0
                units_in_prev_rings = 0

                while soldiers_index >= units_in_prev_rings + (current_ring + 1) * units_per_ring:
                    units_in_prev_rings += (current_ring + 1) * units_per_ring
                    current_ring += 1

                # Position in current ring
                position_in_ring = soldiers_index - units_in_prev_rings
                units_in_this_ring = (current_ring + 1) * units_per_ring

                # Calculate angle and radius
                angle = (position_in_ring / units_in_this_ring) * 2 * math.pi
                radius = (current_ring + 1) * spacing * 0.8

                offset_x = math.cos(angle) * radius
                offset_y = math.sin(angle) * radius

        elif self.type == FormationType.GENERAL_BOX:
            # Rectangle formation - wider and more organized
            # Good for large groups with general
            units_per_row = int(math.sqrt(total_units)) + 1
            row = index // units_per_row
            col = index % units_per_row

            # Create rectangle centered on origin
            offset_x = (col - units_per_row / 2) * spacing * 1.2
            offset_y = (row - (total_units / units_per_row) / 2) * spacing * 1.2

        elif self.type == FormationType.CAPTURE_SPREAD:
            # Spread units evenly in a circle for maximum capture coverage
            # All units at same radius, evenly spaced by angle
            angle = (index / total_units) * 2 * math.pi
            # Radius should be small to fit within base capture radius (100 pixels)
            # Use fixed radius of 60-80 pixels instead of scaling with unit count
            capture_radius = 70  # Fixed radius to fit within base capture zones

            offset_x = math.cos(angle) * capture_radius
            offset_y = math.sin(angle) * capture_radius

        else:
            offset_x = 0
            offset_y = 0

        # Apply looseness variance (random deviation from perfect position)
        if self.looseness > 0:
            variance = spacing * self.looseness * 0.5
            offset_x += random.uniform(-variance, variance)
            offset_y += random.uniform(-variance, variance)

        # Rotate by facing angle
        cos_a = math.cos(facing_angle)
        sin_a = math.sin(facing_angle)
        rotated_x = offset_x * cos_a - offset_y * sin_a
        rotated_y = offset_x * sin_a + offset_y * cos_a

        return (center_x + rotated_x, center_y + rotated_y)

    def calculate_cohesion(self, unit_positions, formation_positions):
        """
        Calculate how well units match their formation positions.
        Returns 0-1, where 1 = perfect formation.
        """
        if len(unit_positions) == 0:
            return 0.0

        total_deviation = 0
        max_acceptable_deviation = self.base_spacing * (1 + self.looseness)

        for unit_pos, formation_pos in zip(unit_positions, formation_positions):
            dx = unit_pos[0] - formation_pos[0]
            dy = unit_pos[1] - formation_pos[1]
            deviation = math.sqrt(dx*dx + dy*dy)
            # Normalize by max acceptable
            normalized_dev = min(1.0, deviation / max_acceptable_deviation)
            total_deviation += normalized_dev

        avg_deviation = total_deviation / len(unit_positions)
        cohesion = 1.0 - avg_deviation

        # Update broken status
        self.is_broken = cohesion < self.break_threshold

        return cohesion

    def choose_formation_for_order(self, order_type, is_general=False):
        """
        Select appropriate formation type based on tactical order.
        Returns new Formation instance.

        Args:
            order_type: Type of order (defend, attack, capture, etc.)
            is_general: True if this is a general's formation
        """
        if order_type == "capture":
            # Capturing base - spread out
            return Formation(FormationType.CAPTURE_SPREAD, looseness=0.5)
        elif order_type == "defend":
            # Defending - protective circle or box
            if is_general:
                return Formation(FormationType.GENERAL_BOX, looseness=0.2)
            else:
                return Formation(FormationType.PROTECTIVE_CIRCLE, looseness=0.2)
        elif order_type == "move" or order_type == "regroup" or order_type == "advance" or order_type == "expand":
            # Moving - general uses box, officers use protective circle
            if is_general:
                return Formation(FormationType.GENERAL_BOX, looseness=0.3)
            else:
                return Formation(FormationType.PROTECTIVE_CIRCLE, looseness=0.3)
        elif order_type == "attack":
            # Attacking - tighter formations
            if is_general:
                return Formation(FormationType.GENERAL_BOX, looseness=0.2)
            else:
                return Formation(FormationType.PROTECTIVE_CIRCLE, looseness=0.2)
        elif order_type == "skirmish":
            return Formation(FormationType.SKIRMISH, looseness=0.8)
        else:
            # Default - protective formations
            if is_general:
                return Formation(FormationType.GENERAL_BOX, looseness=0.3)
            else:
                return Formation(FormationType.PROTECTIVE_CIRCLE, looseness=0.3)


class CommandInfluence:
    """
    Command influence radius system.
    Units dynamically follow nearest commander in range.
    """
    # Command radii by rank
    INFLUENCE_RADIUS = {
        "general": 1000,  # Generals have huge influence (increased from 800)
        "officer": 400,   # Officers command local squads (increased from 300)
        "soldier": 0      # Soldiers don't command
    }

    # Visual aura sizes (for rendering)
    AURA_RADIUS = {
        "general": 800,
        "officer": 300,
    }

    @staticmethod
    def find_nearest_commander(unit_x, unit_y, unit_rank, commanders, max_radius=None):
        """
        Find nearest commander within influence radius.

        Args:
            unit_x, unit_y: Unit position
            unit_rank: "soldier" or "officer"
            commanders: List of (commander_entity, rank, x, y)
            max_radius: Override default influence radius

        Returns:
            (commander_entity, distance) or (None, inf) if none found
        """
        # Determine what rank we're looking for
        if unit_rank == "soldier":
            looking_for = "officer"  # Soldiers follow officers
        elif unit_rank == "officer":
            looking_for = "general"  # Officers follow generals
        else:
            return (None, float('inf'))  # Generals follow no one

        # Get influence radius
        if max_radius is None:
            max_radius = CommandInfluence.INFLUENCE_RADIUS.get(looking_for, 300)

        nearest = None
        nearest_dist = float('inf')

        for commander, rank, cmd_x, cmd_y in commanders:
            if rank != looking_for:
                continue

            dx = cmd_x - unit_x
            dy = cmd_y - unit_y
            dist = math.sqrt(dx*dx + dy*dy)

            if dist <= max_radius and dist < nearest_dist:
                nearest = commander
                nearest_dist = dist

        return (nearest, nearest_dist)

    @staticmethod
    def get_units_in_command_radius(commander_x, commander_y, commander_rank, potential_subordinates):
        """
        Get all units within commander's influence radius.

        Args:
            commander_x, commander_y: Commander position
            commander_rank: "officer" or "general"
            potential_subordinates: List of (entity, rank, x, y)

        Returns:
            List of entities within command radius
        """
        radius = CommandInfluence.INFLUENCE_RADIUS.get(commander_rank, 300)
        radius_sq = radius * radius

        units = []
        for entity, rank, unit_x, unit_y in potential_subordinates:
            # Officers command soldiers, Generals command officers
            if commander_rank == "officer" and rank != "soldier":
                continue
            if commander_rank == "general" and rank != "officer":
                continue

            dx = unit_x - commander_x
            dy = unit_y - commander_y
            dist_sq = dx*dx + dy*dy

            if dist_sq <= radius_sq:
                units.append(entity)

        return units


class FormationManager:
    """
    Manages formations for all squads with regroup logic.
    """
    def __init__(self):
        self.formations = {}  # squad_id -> Formation
        self.formation_centers = {}  # squad_id -> (x, y, facing_angle)
        self.regroup_orders = {}  # squad_id -> regroup_timer

    def create_formation(self, squad_id, formation_type=FormationType.LINE, looseness=0.3):
        """Create or update formation for squad"""
        self.formations[squad_id] = Formation(formation_type, looseness)

    def set_formation_center(self, squad_id, x, y, facing_angle=0):
        """Set the center point and facing for formation"""
        self.formation_centers[squad_id] = (x, y, facing_angle)

    def get_formation_positions(self, squad_id, unit_count):
        """Get ideal positions for all units in formation"""
        if squad_id not in self.formations:
            return []

        formation = self.formations[squad_id]
        center = self.formation_centers.get(squad_id, (0, 0, 0))

        positions = []
        for i in range(unit_count):
            pos = formation.get_position_in_formation(
                i, unit_count, center[0], center[1], center[2]
            )
            positions.append(pos)

        return positions

    def update_cohesion(self, squad_id, unit_positions):
        """
        Update formation cohesion and check if regroup needed.
        Returns cohesion value (0-1).
        """
        if squad_id not in self.formations:
            return 1.0

        formation = self.formations[squad_id]
        formation_positions = self.get_formation_positions(squad_id, len(unit_positions))

        cohesion = formation.calculate_cohesion(unit_positions, formation_positions)

        # If formation broke, issue regroup order
        if formation.is_broken and squad_id not in self.regroup_orders:
            self.issue_regroup(squad_id)

        return cohesion

    def issue_regroup(self, squad_id, duration=3.0):
        """
        Issue regroup order - squad halts other activities to reform.
        Duration: how long to spend regrouping before resuming objectives.
        """
        self.regroup_orders[squad_id] = duration

        # Switch to column formation for regrouping (easier to reform)
        self.create_formation(squad_id, FormationType.COLUMN, looseness=0.5)

    def is_regrouping(self, squad_id):
        """Check if squad is currently regrouping"""
        return squad_id in self.regroup_orders

    def update_regroup(self, squad_id, dt):
        """Update regroup timer"""
        if squad_id in self.regroup_orders:
            self.regroup_orders[squad_id] -= dt
            if self.regroup_orders[squad_id] <= 0:
                del self.regroup_orders[squad_id]
                return True  # Regroup complete
        return False

    def change_formation_for_order(self, squad_id, order_type):
        """Change formation type based on tactical order"""
        formation = Formation.choose_formation_for_order(Formation, order_type)
        self.formations[squad_id] = formation
