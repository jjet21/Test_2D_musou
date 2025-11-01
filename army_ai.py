"""
Strategic and Tactical AI for army command
General AI: Macro-level strategy with reserves
Officer AI: Tactical squad management with threat evaluation
"""
import math
import random


class GeneralAI:
    """
    Strategic AI for generals.
    - Analyzes battlefield state
    - Issues high-level orders to officers
    - Manages reserve pool
    - Weights objectives by strategic value
    """
    def __init__(self, team_id, blackboard, formation_manager):
        self.team_id = team_id
        self.blackboard = blackboard
        self.formation_manager = formation_manager

        # Strategic state
        self.current_strategy = "advance"  # "attack", "defend", "advance", "retreat"
        self.decision_cooldown = 2.0  # Re-evaluate strategy every 2 seconds
        self.decision_timer = 0.0

        # Reserve management
        self.reserve_squads = []
        self.active_squads = []

        # Objective priorities (base_name -> importance_multiplier)
        self.objective_priorities = {}

        # Game time tracking
        self.game_time = 0.0

        # General repositioning
        self.current_position = None  # (x, y) of general
        self.target_position = None   # Where general should move to
        self.last_owned_bases = 0     # Track base loss
        self.repositioning_threshold = 400  # Move if center of mass shifts by this much

    def set_objective_priority(self, base_name, multiplier):
        """Set strategic value of objective (1.0 = normal, >1.0 = high value)"""
        self.objective_priorities[base_name] = multiplier

    def update(self, dt, entity_manager, general_entity, objective_system, game_time=0.0):
        """Update strategic decision making"""
        self.game_time = game_time
        self.decision_timer += dt

        # Update general's current position
        transform = general_entity.get_component("Transform")
        if transform:
            self.current_position = (transform.x, transform.y)

        if self.decision_timer >= self.decision_cooldown:
            self.decision_timer = 0.0
            self.make_strategic_decision(entity_manager, general_entity, objective_system)

            # Check if general needs to reposition
            self.check_repositioning_needed(entity_manager, general_entity, objective_system)

        # Check if reserves should be committed
        if self.should_commit_reserves():
            self.commit_one_reserve_squad()

        # Execute repositioning if needed
        if self.target_position and transform:
            self.move_general_to_position(transform, dt)
        else:
            # No active repositioning - gently drift toward strategic objective
            self.drift_toward_objective(entity_manager, transform, dt)

    def make_strategic_decision(self, entity_manager, general_entity, objective_system):
        """
        Main strategic decision loop.
        Analyzes battlefield and issues orders to officers.
        """
        # Update team statistics
        self.blackboard.update_team_stats(self.team_id, entity_manager)
        team_stats = self.blackboard.get_team_stats(self.team_id)
        enemy_stats = self.blackboard.get_team_stats(1 - self.team_id)

        print(f"[GENERAL TEAM {self.team_id}] Units: {team_stats['total_units']}, Enemy: {enemy_stats['total_units']}")

        # Evaluate base ownership
        player_bases = len(objective_system.get_player_bases() if self.team_id == 0
                          else objective_system.get_enemy_bases())
        enemy_bases = len(objective_system.get_enemy_bases() if self.team_id == 0
                         else objective_system.get_player_bases())
        neutral_bases = len(objective_system.get_neutral_bases())

        # Strategic decision tree with weighted objectives
        if player_bases == 0 and enemy_bases > 0:
            # Desperate - we have no bases, attack nearest
            self.current_strategy = "desperate_attack"
            target = self.choose_target_objective(objective_system, strategy="nearest", entity_manager=entity_manager)

        elif enemy_bases > player_bases:
            # Losing map control - attack enemy base (prioritize high-value targets)
            self.current_strategy = "attack"
            target = self.choose_target_objective(objective_system, strategy="weighted_enemy", entity_manager=entity_manager)

        elif neutral_bases > 0:
            # Expand - capture neutral bases
            self.current_strategy = "expand"
            target = self.choose_target_objective(objective_system, strategy="weighted_neutral", entity_manager=entity_manager)

        elif team_stats["total_units"] < enemy_stats["total_units"] * 0.7:
            # Numerically inferior - defend our bases
            self.current_strategy = "defend"
            target = self.choose_defensive_position(objective_system)

        else:
            # Winning - advance and pressure
            self.current_strategy = "advance"
            target = self.choose_target_objective(objective_system, strategy="weighted_enemy", entity_manager=entity_manager)

        # Issue strategic goal to blackboard
        self.blackboard.set_strategic_goal(self.team_id, self.current_strategy, target)

        # Debug output
        if target:
            print(f"[GENERAL TEAM {self.team_id}] Strategy: {self.current_strategy}, Target: {target.name} at ({int(target.x)}, {int(target.y)})")
        else:
            print(f"[GENERAL TEAM {self.team_id}] Strategy: {self.current_strategy}, No target")

        # Assign squads to objectives
        self.assign_squads_to_objectives(entity_manager)

    def choose_target_objective(self, objective_system, strategy="nearest", entity_manager=None):
        """
        Choose target base with strategic value weighting and distance factor.
        """
        if strategy == "nearest":
            # Simple: attack nearest enemy base
            if self.team_id == 0:
                bases = objective_system.get_enemy_bases()
            else:
                bases = objective_system.get_player_bases()

        elif strategy == "weighted_enemy":
            # Weighted: prioritize high-value enemy bases
            if self.team_id == 0:
                bases = objective_system.get_enemy_bases()
            else:
                bases = objective_system.get_player_bases()

        elif strategy == "weighted_neutral":
            # Capture high-value neutral bases first
            bases = objective_system.get_neutral_bases()

        else:
            bases = objective_system.bases

        if not bases:
            return None

        # Calculate army center of mass for distance calculations
        army_center_x, army_center_y = self._calculate_army_center(entity_manager)

        # Score each base: strategic_value / (distance_factor)
        # This makes closer bases more attractive, especially for similar strategic values
        def score_base(base):
            strategic_value = self.objective_priorities.get(base.name, 1.0)

            if army_center_x is not None:
                dx = base.x - army_center_x
                dy = base.y - army_center_y
                distance = math.sqrt(dx*dx + dy*dy)
                # Normalize distance: divide by 1000 to get a 0-3 range typically
                # Add 0.5 to prevent division by zero and avoid over-prioritizing super close bases
                distance_factor = (distance / 1000.0) + 0.5

                # Score = strategic value / distance factor
                # Higher strategic value = higher score
                # Lower distance = higher score
                return strategic_value / distance_factor
            else:
                # No army center, just use strategic value
                return strategic_value

        # Sort by score (highest first)
        bases = sorted(bases, key=score_base, reverse=True)
        return bases[0]

    def _calculate_army_center(self, entity_manager):
        """Calculate center of mass of army (officers + general)"""
        if not entity_manager:
            return None, None

        officers = [e for e in entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(f"team_{self.team_id}")]

        generals = [e for e in entity_manager.get_entities_with_tag("general")
                   if e.active and e.has_tag(f"team_{self.team_id}")]

        all_commanders = officers + generals

        if not all_commanders:
            return None, None

        total_x = 0
        total_y = 0
        count = 0

        for commander in all_commanders:
            transform = commander.get_component("Transform")
            if transform:
                total_x += transform.x
                total_y += transform.y
                count += 1

        if count == 0:
            return None, None

        return total_x / count, total_y / count

    def choose_defensive_position(self, objective_system):
        """Choose best base to defend"""
        if self.team_id == 0:
            our_bases = objective_system.get_player_bases()
        else:
            our_bases = objective_system.get_enemy_bases()

        if not our_bases:
            return None

        # Defend highest-value base we own
        our_bases = sorted(our_bases,
                          key=lambda b: self.objective_priorities.get(b.name, 1.0),
                          reverse=True)
        return our_bases[0]

    def assign_squads_to_objectives(self, entity_manager):
        """Assign officer squads to tactical objectives"""
        officers = [e for e in entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(f"team_{self.team_id}")]

        strategic_goal = self.blackboard.get_strategic_goal(self.team_id)
        if not strategic_goal:
            return

        target = strategic_goal["target"]
        if not target:
            return

        # Divide officers between active and reserve
        total_officers = len(officers)
        reserve_count = max(1, int(total_officers * 0.3))  # 30% reserve

        # Keep some squads in reserve (if not desperate)
        if self.current_strategy != "desperate_attack":
            self.reserve_squads = officers[:reserve_count]
            self.active_squads = officers[reserve_count:]
        else:
            self.reserve_squads = []
            self.active_squads = officers

        # Assign active squads to target
        for officer in self.active_squads:
            unit = officer.get_component("Unit")
            if unit and unit.squad_id:
                # Officer receives order via blackboard
                order = {
                    "type": self.current_strategy,
                    "target": (target.x, target.y),
                    "priority": self.objective_priorities.get(target.name, 1.0)
                }
                self.blackboard.issue_order(
                    officer.id, order, "general_to_officer", self.game_time
                )

    def should_commit_reserves(self):
        """Check if conditions warrant committing reserves"""
        team_stats = self.blackboard.get_team_stats(self.team_id)
        enemy_stats = self.blackboard.get_team_stats(1 - self.team_id)

        # Commit if numerically inferior
        if team_stats["total_units"] < enemy_stats["total_units"] * 0.8:
            return True

        # Commit if losing morale
        if self.blackboard.get_morale(self.team_id) < 0.4:
            return True

        return False

    def commit_one_reserve_squad(self):
        """Move one squad from reserve to active"""
        if self.reserve_squads:
            officer = self.reserve_squads.pop(0)
            self.active_squads.append(officer)
            # Issue order to newly committed squad
            strategic_goal = self.blackboard.get_strategic_goal(self.team_id)
            if strategic_goal and strategic_goal["target"]:
                target = strategic_goal["target"]
                order = {
                    "type": "attack",  # Reserves commit aggressively
                    "target": (target.x, target.y),
                    "priority": 2.0  # High priority
                }
                self.blackboard.issue_order(officer.id, order, "general_to_officer", self.game_time)

    def check_repositioning_needed(self, entity_manager, general_entity, objective_system):
        """Check if general needs to reposition based on strategic situation"""
        if not self.current_position:
            return

        # Calculate ideal position (center of mass of officers)
        officers = [e for e in entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(f"team_{self.team_id}")]

        if not officers:
            return  # No officers, stay put

        # Calculate center of mass
        total_x = 0
        total_y = 0
        count = 0

        for officer in officers:
            transform = officer.get_component("Transform")
            if transform:
                total_x += transform.x
                total_y += transform.y
                count += 1

        if count == 0:
            return

        center_x = total_x / count
        center_y = total_y / count

        # Calculate distance from current position to center
        dx = center_x - self.current_position[0]
        dy = center_y - self.current_position[1]
        distance = math.sqrt(dx*dx + dy*dy)

        # Check triggers for repositioning
        current_owned_bases = len(objective_system.get_player_bases() if self.team_id == 0
                                  else objective_system.get_enemy_bases())

        # Trigger 1: Lost bases
        base_lost = current_owned_bases < self.last_owned_bases
        self.last_owned_bases = current_owned_bases

        # Trigger 2: Army center of mass shifted significantly
        army_shifted = distance > self.repositioning_threshold

        # Trigger 3: General is very far from army
        general_too_far = distance > 600

        if base_lost or army_shifted or general_too_far:
            # Reposition general to center of officers (stay slightly behind)
            strategic_goal = self.blackboard.get_strategic_goal(self.team_id)
            if strategic_goal and strategic_goal["target"]:
                target = strategic_goal["target"]
                # Position between officers and objective (closer to officers)
                target_x = center_x * 0.8 + target.x * 0.2
                target_y = center_y * 0.8 + target.y * 0.2
            else:
                target_x = center_x
                target_y = center_y

            self.target_position = (target_x, target_y)
            print(f"[GENERAL TEAM {self.team_id}] Repositioning! Triggers: base_lost={base_lost}, shifted={army_shifted}, too_far={general_too_far}")

    def move_general_to_position(self, transform, dt):
        """Move general toward target position"""
        if not self.target_position:
            return

        dx = self.target_position[0] - transform.x
        dy = self.target_position[1] - transform.y
        distance = math.sqrt(dx*dx + dy*dy)

        # Stop if close enough
        if distance < 50:
            transform.vx = 0
            transform.vy = 0
            self.target_position = None  # Repositioning complete
            print(f"[GENERAL TEAM {self.team_id}] Repositioning complete")
            return

        # Move slowly toward target
        general_speed = 50  # Generals move slowly
        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance
            transform.vx = direction_x * general_speed
            transform.vy = direction_y * general_speed

            # Apply movement
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt

    def drift_toward_objective(self, entity_manager, transform, dt):
        """Gently drift toward strategic objective when not actively repositioning"""
        if not transform:
            return

        strategic_goal = self.blackboard.get_strategic_goal(self.team_id)
        if not strategic_goal or not strategic_goal["target"]:
            transform.vx = 0
            transform.vy = 0
            return

        target = strategic_goal["target"]

        # Calculate center of mass of officers
        officers = [e for e in entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(f"team_{self.team_id}")]

        if not officers:
            transform.vx = 0
            transform.vy = 0
            return

        # Calculate officer center
        officer_x_sum = 0
        officer_y_sum = 0
        count = 0
        for officer in officers:
            off_transform = officer.get_component("Transform")
            if off_transform:
                officer_x_sum += off_transform.x
                officer_y_sum += off_transform.y
                count += 1

        if count == 0:
            transform.vx = 0
            transform.vy = 0
            return

        center_x = officer_x_sum / count
        center_y = officer_y_sum / count

        # Position 70% toward officers, 30% toward objective (stay behind but advance)
        ideal_x = center_x * 0.7 + target.x * 0.3
        ideal_y = center_y * 0.7 + target.y * 0.3

        # Move toward ideal position if far enough
        dx = ideal_x - transform.x
        dy = ideal_y - transform.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > 200:  # Only move if significantly far
            general_drift_speed = 30  # Very slow drift
            direction_x = dx / distance
            direction_y = dy / distance
            transform.vx = direction_x * general_drift_speed
            transform.vy = direction_y * general_drift_speed

            transform.x += transform.vx * dt
            transform.y += transform.vy * dt
        else:
            # Close enough, hold position
            transform.vx = 0
            transform.vy = 0


class OfficerAI:
    """
    Tactical AI for officers.
    - Commands squad of soldiers
    - Evaluates local threats
    - Maintains formation
    - Requests reinforcements when needed
    """
    def __init__(self, squad_id, blackboard, formation_manager, entity_manager):
        self.squad_id = squad_id
        self.blackboard = blackboard
        self.formation_manager = formation_manager
        self.entity_manager = entity_manager

        # Tactical state
        self.current_order = None  # "attack", "defend", "move", "retreat"
        self.target_position = None
        self.formation_type = "line"

        # Threat evaluation
        self.local_threat_ratio = 0.0
        self.retreat_threshold = 1.5
        self.evaluation_cooldown = 1.0
        self.evaluation_timer = 0.0

        # Reinforcement
        self.reinforcement_requested = False
        self.reinforcement_threshold = 0.4

        # Game time tracking
        self.game_time = 0.0

        # Combat participation
        self.should_officer_join_combat = False

        # Scout system
        self.scouts_deployed = False
        self.scout_decision_cooldown = 5.0  # Re-evaluate scouts every 5 seconds
        self.scout_decision_timer = 0.0
        self.max_scout_percent = 0.10  # 10% max
        self.min_squad_for_scouts = 5  # Need at least 5 soldiers

    def update(self, dt, entity_manager, officer_entity, game_time=0.0, objective_system=None):
        """Update tactical decision making"""
        self.game_time = game_time
        self.evaluation_timer += dt
        self.entity_manager = entity_manager

        # Check for new orders from general
        orders = self.blackboard.get_orders_for_unit(officer_entity.id, self.game_time)
        for order in orders:
            self.process_order(order)

        # Periodic threat evaluation
        if self.evaluation_timer >= self.evaluation_cooldown:
            self.evaluation_timer = 0.0
            self.evaluate_and_act(entity_manager, officer_entity)

        # Scout management (evaluate every 5 seconds)
        self.scout_decision_timer += dt
        if self.scout_decision_timer >= self.scout_decision_cooldown:
            self.scout_decision_timer = 0.0
            self.manage_scouts(entity_manager, officer_entity)

        # CRITICAL: Move officer toward target objective (with threat-based tactics)
        self.move_toward_objective(officer_entity, dt, objective_system)

        # Update formation positions
        self.update_squad_formation(entity_manager, officer_entity)

    def process_order(self, order):
        """Process order from general"""
        self.current_order = order["type"]
        self.target_position = order["target"]

        # Debug output
        if self.target_position:
            print(f"[OFFICER {self.squad_id}] Received order: {self.current_order}, Target: ({int(self.target_position[0])}, {int(self.target_position[1])})")

        # Change formation based on order
        self.formation_manager.change_formation_for_order(self.squad_id, self.current_order)

    def evaluate_and_act(self, entity_manager, officer_entity):
        """
        Evaluate local situation and make tactical decisions.
        """
        transform = officer_entity.get_component("Transform")
        unit = officer_entity.get_component("Unit")

        if not transform or not unit:
            return

        # Evaluate local threat
        self.local_threat_ratio = self.blackboard.calculate_local_superiority(
            unit.team, transform.x, transform.y, 400, entity_manager
        )

        # Convert superiority to threat ratio
        if self.local_threat_ratio > 0.5:
            threat_ratio = (1.0 - self.local_threat_ratio) / self.local_threat_ratio
        else:
            threat_ratio = 999.0 if self.local_threat_ratio == 0 else \
                          self.local_threat_ratio / (1.0 - self.local_threat_ratio)

        # Get squad info
        squad_info = self.blackboard.get_squad_info(self.squad_id)
        if not squad_info:
            return

        squad_size = len(squad_info["soldier_ids"])
        max_size = squad_info["max_size"]

        # Check squad morale (based on casualties)
        squad_strength_ratio = squad_size / max_size if max_size > 0 else 0
        squad_morale = squad_strength_ratio  # Simple: morale = strength

        # Decision: Should we retreat?
        if threat_ratio > self.retreat_threshold or squad_morale < 0.3:
            if self.current_order != "retreat":
                self.initiate_retreat()

        # Decision: Should we request reinforcements?
        if squad_strength_ratio < self.reinforcement_threshold and not self.reinforcement_requested:
            self.request_reinforcements(officer_entity)

        # Decision: Should we regroup?
        cohesion = self.blackboard.get_cohesion(self.squad_id)
        if cohesion < 0.3 and not self.formation_manager.is_regrouping(self.squad_id):
            self.formation_manager.issue_regroup(self.squad_id)

    def initiate_retreat(self):
        """Tactical retreat"""
        self.current_order = "retreat"
        # TODO: Find safe fallback position
        self.formation_manager.change_formation_for_order(self.squad_id, "move")

    def request_reinforcements(self, officer_entity):
        """Request reinforcements from general"""
        transform = officer_entity.get_component("Transform")
        unit = officer_entity.get_component("Unit")

        if transform and unit:
            # Write request to blackboard
            # (General AI will check this)
            self.reinforcement_requested = True

    def calculate_combat_participation(self, threat_level, unit):
        """Decide if officer should join combat based on threat and morale"""
        # Officers stay back by default
        # Only join if squad morale is low or threat is high and their help would tip the balance

        squad_info = self.blackboard.get_squad_info(self.squad_id)
        if not squad_info:
            return False

        squad_size = len(squad_info["soldier_ids"])
        squad_morale = unit.morale if hasattr(unit, 'morale') else 1.0

        # Join combat if:
        # 1. Threat is high AND morale is decent (officer inspires troops)
        # 2. Threat is medium AND squad is small (need every fighter)
        # 3. Morale is low (officer leads by example to boost morale)

        if threat_level == "overwhelming":
            # Too dangerous - officer should not risk themselves
            return False
        elif threat_level == "high":
            # Only join if morale is good (can turn the tide)
            return squad_morale > 0.6
        elif threat_level == "medium":
            # Join if squad is small
            return squad_size < 6
        elif squad_morale < 0.4:
            # Low morale - lead from front to inspire
            return True
        else:
            # Low threat, good morale - stay back and command
            return False

    def calculate_capture_priority(self, capture_progress, threat_level, team):
        """Calculate capture priority with exponential scaling (0%=1.0x, 50%=2.5x, 90%=4.0x)"""
        # Normalize progress for this team (0.0-1.0 where 1.0 = fully captured by this team)
        if team == 0:
            # Team 0: progress > 0.7 = owned, closer to 1.0 = more complete
            team_progress = max(0, (capture_progress - 0.5) * 2.0)  # Map 0.5-1.0 to 0.0-1.0
        else:
            # Team 1: progress < 0.3 = owned, closer to 0.0 = more complete
            team_progress = max(0, (0.5 - capture_progress) * 2.0)  # Map 0.5-0.0 to 0.0-1.0

        # Exponential progress bonus: bonus = 1.0 + progress^2 * 3.0
        # At 0%: 1.0 + 0.0 = 1.0x
        # At 50%: 1.0 + 0.25 * 3.0 = 1.75x
        # At 70%: 1.0 + 0.49 * 3.0 = 2.47x
        # At 90%: 1.0 + 0.81 * 3.0 = 3.43x
        # At 100%: 1.0 + 1.0 * 3.0 = 4.0x
        progress_bonus = 1.0 + (team_progress ** 2) * 3.0

        # Threat penalty
        threat_modifiers = {
            "low": 0.0,
            "medium": 0.3,
            "high": 0.6,
            "overwhelming": 1.0
        }
        threat_penalty = threat_modifiers.get(threat_level, 0.5)

        base_priority = 1.0
        final_priority = base_priority * progress_bonus * (1.0 - threat_penalty)

        return final_priority

    def calculate_combat_priority(self, threat_level, unit):
        """Calculate combat priority based on threat"""
        squad_morale = unit.morale if hasattr(unit, 'morale') else 1.0

        if threat_level == "low":
            return 0.3  # Can mostly ignore
        elif threat_level == "medium":
            return 0.8  # Should fight but not critical
        elif threat_level == "high":
            return 1.5 * squad_morale  # Must fight if morale is good
        else:  # overwhelming
            return 0.0  # Don't fight, retreat!

    def calculate_retreat_priority(self, threat_level, unit):
        """Calculate retreat priority based on threat and morale"""
        squad_morale = unit.morale if hasattr(unit, 'morale') else 1.0

        if threat_level == "overwhelming":
            return 2.0  # Always retreat
        elif threat_level == "high" and squad_morale < 0.4:
            return 1.8  # Morale broken
        elif threat_level == "medium" and squad_morale < 0.2:
            return 1.5  # Panic retreat
        else:
            return 0.0  # Hold ground

    def should_abandon_objective(self, threat_level, unit):
        """Decide if objective should be abandoned due to overwhelming odds"""
        if threat_level == "overwhelming":
            # Check morale - broken units always retreat
            squad_morale = unit.morale if hasattr(unit, 'morale') else 1.0
            if squad_morale < 0.3:
                return True  # Morale broken, retreat

            # Check if we have reinforcements coming
            # (Could check blackboard for nearby friendly squads)
            # For now, retreat if morale isn't excellent
            return squad_morale < 0.7

        return False  # Don't abandon unless overwhelming

    def move_toward_objective(self, officer_entity, dt, objective_system=None):
        """Move officer toward assigned objective with threat-based tactics"""
        transform = officer_entity.get_component("Transform")
        unit = officer_entity.get_component("Unit")

        if not transform or not unit:
            return

        # CHECK: Is current objective already captured by our team?
        if self.target_position and objective_system:
            # Find which base we're targeting
            target_x, target_y = self.target_position
            for base in objective_system.bases:
                dx = base.x - target_x
                dy = base.y - target_y
                if math.sqrt(dx*dx + dy*dy) < 50:  # This is our target base
                    # Check if we already own it
                    if base.owner == unit.team:
                        print(f"[OFFICER {self.squad_id}] Objective {base.name} already captured! Looking for new target...")
                        self.target_position = None
                        break

        # FALLBACK: If no target assigned, look for strategic goal from blackboard
        if not self.target_position:
            strategic_goal = self.blackboard.get_strategic_goal(unit.team)
            if strategic_goal and strategic_goal["target"]:
                target = strategic_goal["target"]
                # Only adopt target if we don't already own it
                if target.owner != unit.team:
                    self.target_position = (target.x, target.y)
                    self.current_order = strategic_goal["objective"]
                    print(f"[OFFICER {self.squad_id}] Adopting strategic goal: {self.current_order} -> {target.name}")
                else:
                    print(f"[OFFICER {self.squad_id}] Strategic target {target.name} already owned, waiting for new orders...")

        if not self.target_position:
            # Still no target - defensive idle
            transform.vx = 0
            transform.vy = 0
            return

        # Calculate direction to target
        target_x, target_y = self.target_position
        dx = target_x - transform.x
        dy = target_y - transform.y
        distance = math.sqrt(dx*dx + dy*dy)

        # Check threat level at current position
        threat_level = self.blackboard.calculate_threat_level(
            unit.team, transform.x, transform.y, 300, self.entity_manager
        )

        # TACTICAL DECISION: Are we near a base?
        near_base = False
        nearest_base = None
        base_distance = float('inf')

        if objective_system:
            for base in objective_system.bases:
                base_dx = base.x - transform.x
                base_dy = base.y - transform.y
                base_dist = math.sqrt(base_dx*base_dx + base_dy*base_dy)

                if base_dist < base.radius + 150:  # Within capture proximity
                    near_base = True
                    if base_dist < base_distance:
                        nearest_base = base
                        base_distance = base_dist

        # TACTICAL FORMATION SWITCHING WITH EXPONENTIAL CAPTURE PRIORITY
        if near_base and nearest_base:
            # Calculate capture priority (exponential with progress)
            capture_priority = self.calculate_capture_priority(
                nearest_base.capture_progress, threat_level, unit.team
            )
            combat_priority = self.calculate_combat_priority(threat_level, unit)
            retreat_priority = self.calculate_retreat_priority(threat_level, unit)

            # Decide action based on priorities
            if retreat_priority > capture_priority and retreat_priority > combat_priority:
                # RETREAT
                print(f"[TACTICAL] {self.squad_id} retreating! (retreat_priority={retreat_priority:.2f})")
                self.target_position = None
                return
            elif combat_priority > capture_priority:
                # COMBAT - abandon capture, fight enemies
                print(f"[TACTICAL] {self.squad_id} prioritizing combat over capture (combat={combat_priority:.2f} vs capture={capture_priority:.2f})")
                self.formation_manager.change_formation_for_order(self.squad_id, "defend")
                # Don't move toward base, hold position or engage
            else:
                # CAPTURE - continue toward objective
                if threat_level == "low":
                    # Spread out for maximum capture
                    self.formation_manager.change_formation_for_order(self.squad_id, "capture")
                    # Always move to base center for optimal capture positioning
                    self.target_position = (nearest_base.x, nearest_base.y)
                elif threat_level == "medium":
                    # Defensive formation but still capture
                    self.formation_manager.change_formation_for_order(self.squad_id, "defend")
                    # Move toward base but maintain defensive posture
                    if base_distance > nearest_base.radius * 0.3:
                        self.target_position = (nearest_base.x, nearest_base.y)
                else:
                    # High threat but capture priority is still higher - defensive capture
                    self.formation_manager.change_formation_for_order(self.squad_id, "defend")
                    if base_distance > nearest_base.radius * 0.3:
                        self.target_position = (nearest_base.x, nearest_base.y)

        # Decide if officer should participate in combat or stay back
        self.should_officer_join_combat = self.calculate_combat_participation(threat_level, unit)

        # OFFICER POSITIONING: Slightly behind soldiers unless needed in front
        officer_offset = -30 if not self.should_officer_join_combat else 0

        # Stop if close enough to target (smaller threshold when capturing)
        stop_distance = 30 if near_base else 100  # Get closer to base centers
        if distance < stop_distance:
            transform.vx = 0
            transform.vy = 0
            return

        # Move toward target
        officer_speed = 80  # Officers move slower than soldiers to maintain formation
        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance

            # Apply officer offset (stay slightly behind)
            transform.vx = direction_x * officer_speed
            transform.vy = direction_y * officer_speed

            # Apply movement
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt

    def update_squad_formation(self, entity_manager, officer_entity):
        """Update formation positions for squad soldiers"""
        transform = officer_entity.get_component("Transform")
        if not transform:
            return

        # Set formation center at officer position
        self.formation_manager.set_formation_center(
            self.squad_id, transform.x, transform.y, 0
        )

        # Get squad soldiers
        squad_info = self.blackboard.get_squad_info(self.squad_id)
        if not squad_info:
            return

        soldier_ids = squad_info["soldier_ids"]

        # Get formation positions
        formation_positions = self.formation_manager.get_formation_positions(
            self.squad_id, len(soldier_ids)
        )

        # Assign positions to each soldier's Unit component
        for soldier_id, (form_x, form_y) in zip(soldier_ids, formation_positions):
            # Find soldier entity
            soldier = None
            for e in entity_manager.entities:
                if e.id == soldier_id and e.active:
                    soldier = e
                    break

            if soldier:
                unit = soldier.get_component("Unit")
                if unit:
                    unit.formation_position = (form_x, form_y)

    def manage_scouts(self, entity_manager, officer_entity):
        """Manage scout deployment based on threat and squad size"""
        transform = officer_entity.get_component("Transform")
        unit = officer_entity.get_component("Unit")

        if not transform or not unit:
            return

        # Get squad info
        squad_info = self.blackboard.get_squad_info(self.squad_id)
        if not squad_info:
            return

        soldier_ids = squad_info["soldier_ids"]
        squad_size = len(soldier_ids)

        # Check if we should deploy scouts
        threat_level = self.blackboard.calculate_threat_level(
            unit.team, transform.x, transform.y, 400, entity_manager
        )

        should_deploy = self.should_deploy_scouts(threat_level, squad_size)

        if should_deploy and not self.scouts_deployed:
            # Deploy scouts
            max_scouts = self.calculate_max_scouts(squad_size)
            if max_scouts > 0:
                self.deploy_scouts(soldier_ids[:max_scouts], transform)
                self.scouts_deployed = True
                print(f"[OFFICER {self.squad_id}] Deployed {max_scouts} scouts (squad size: {squad_size})")

        elif not should_deploy and self.scouts_deployed:
            # Recall scouts
            self.blackboard.recall_scouts(self.squad_id)
            self.scouts_deployed = False
            print(f"[OFFICER {self.squad_id}] Recalled scouts (threat level: {threat_level})")

    def calculate_max_scouts(self, squad_size):
        """Calculate maximum number of scouts allowed"""
        if squad_size < self.min_squad_for_scouts:
            return 0  # No scouts if squad too small

        max_by_percent = int(squad_size * self.max_scout_percent)
        return max(1, max_by_percent)  # Minimum 1 if allowed

    def should_deploy_scouts(self, threat_level, squad_size):
        """Decide if scouts should be deployed"""
        if squad_size < self.min_squad_for_scouts:
            return False

        # Deploy scouts when threat is low or medium
        # Don't deploy during high threat or combat
        return threat_level in ["low", "medium"]

    def deploy_scouts(self, scout_ids, officer_transform):
        """Deploy scouts with patrol positions around officer"""
        num_scouts = len(scout_ids)
        if num_scouts == 0:
            return

        patrol_positions = []
        patrol_radius = 250  # Scouts patrol 250 pixels from officer

        # Scouts patrol in circle around officer
        for i in range(num_scouts):
            angle = (i / num_scouts) * 2 * math.pi
            patrol_x = officer_transform.x + math.cos(angle) * patrol_radius
            patrol_y = officer_transform.y + math.sin(angle) * patrol_radius
            patrol_positions.append((patrol_x, patrol_y))

        # Assign scouts to blackboard
        self.blackboard.assign_scouts(self.squad_id, scout_ids, patrol_positions)
