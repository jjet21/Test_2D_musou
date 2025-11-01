"""
Soldier AI - Formation following and squad coordination
"""
import math
from game.formation import CommandInfluence


class SoldierAI:
    """
    AI for individual soldiers.
    - Follow nearest officer
    - Maintain formation position
    - Engage nearby enemies
    - Obey morale modifiers
    """
    def __init__(self, entity_manager, blackboard, formation_manager):
        self.entity_manager = entity_manager
        self.blackboard = blackboard
        self.formation_manager = formation_manager

        # AI parameters
        self.formation_seek_strength = 0.7  # How strongly to seek formation position
        self.combat_seek_strength = 0.3     # How strongly to seek enemies
        self.formation_tolerance = 30       # "Good enough" distance from ideal position

    def update(self, dt, soldier_entity):
        """Update soldier behavior"""
        transform = soldier_entity.get_component("Transform")
        unit = soldier_entity.get_component("Unit")
        combat = soldier_entity.get_component("Combat")
        health = soldier_entity.get_component("Health")

        if not transform or not unit or not combat or not health:
            return

        # Skip if dead
        if health.dead:
            return

        # Find commanding officer
        officer = self.find_commanding_officer(soldier_entity)

        if officer:
            # We have a commander - follow formation
            self.follow_formation(soldier_entity, officer, transform, unit, combat, dt)
        else:
            # No commander nearby - default wander/defensive behavior
            self.default_behavior(soldier_entity, transform, unit, combat, dt)

    def find_commanding_officer(self, soldier_entity):
        """Find nearest officer within command radius"""
        transform = soldier_entity.get_component("Transform")
        unit = soldier_entity.get_component("Unit")

        if not transform or not unit:
            return None

        # Get all officers from same team
        team_tag = f"team_{unit.team}"
        officers = [e for e in self.entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(team_tag)]

        # Build commander list
        commanders = []
        for officer in officers:
            off_transform = officer.get_component("Transform")
            if off_transform:
                commanders.append((officer, "officer", off_transform.x, off_transform.y))

        # Find nearest in radius
        nearest, dist = CommandInfluence.find_nearest_commander(
            transform.x, transform.y, "soldier", commanders
        )

        return nearest

    def follow_formation(self, soldier_entity, officer, transform, unit, combat, dt):
        """Follow officer's formation and engage enemies"""
        # Check if this soldier is a scout
        if self.blackboard.is_scout(soldier_entity.id):
            self.scout_patrol_behavior(soldier_entity, transform, unit, combat, dt)
            return

        # Get squad assignment
        squad_id = unit.squad_id

        # Get formation position if assigned
        if unit.formation_position:
            target_x, target_y = unit.formation_position

            # Calculate distance to formation position
            dx = target_x - transform.x
            dy = target_y - transform.y
            distance_to_formation = math.sqrt(dx*dx + dy*dy)

            # Update formation deviation (for cohesion tracking)
            unit.formation_deviation = distance_to_formation

            # Look for priority target (protection > high-rank enemies > nearest)
            nearest_enemy, nearest_enemy_dist = self.select_priority_target(
                soldier_entity, transform, unit, combat
            )

            # Decision: Formation vs Combat
            if nearest_enemy and nearest_enemy_dist < combat.attack_range * 2:
                # Enemy very close - engage
                self.engage_enemy(transform, nearest_enemy, combat, dt)

            elif distance_to_formation > self.formation_tolerance:
                # Not in position - move to formation
                if distance_to_formation > 0:
                    # Move toward formation position
                    move_speed = 120 * unit.get_combat_modifier()  # Morale affects movement
                    direction_x = dx / distance_to_formation
                    direction_y = dy / distance_to_formation
                    transform.vx = direction_x * move_speed
                    transform.vy = direction_y * move_speed

                    # Update position
                    transform.x += transform.vx * dt
                    transform.y += transform.vy * dt

            elif nearest_enemy and nearest_enemy_dist < combat.attack_range * 3:
                # In formation, enemy in range - engage while maintaining position
                self.engage_enemy(transform, nearest_enemy, combat, dt)

            else:
                # In formation, no immediate threats - hold position
                transform.vx = 0
                transform.vy = 0

        else:
            # No formation position assigned - move toward officer
            officer_transform = officer.get_component("Transform")
            if officer_transform:
                dx = officer_transform.x - transform.x
                dy = officer_transform.y - transform.y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 100:  # Not too close to officer
                    move_speed = 100
                    if distance > 0:
                        direction_x = dx / distance
                        direction_y = dy / distance
                        transform.vx = direction_x * move_speed
                        transform.vy = direction_y * move_speed

                        transform.x += transform.vx * dt
                        transform.y += transform.vy * dt
                else:
                    transform.vx = 0
                    transform.vy = 0

    def select_priority_target(self, soldier_entity, transform, unit, combat):
        """
        Select target based on priorities:
        1. Protect friendly commanders under threat (general > officer > self)
        2. Target high-rank enemies (general > officer > soldier)
        3. Fall back to nearest enemy

        Returns: (target_entity, distance) or (None, inf)
        """
        enemy_team = 1 - unit.team
        friendly_team = unit.team
        enemy_tag = f"team_{enemy_team}"
        friendly_tag = f"team_{friendly_team}"

        detection_range = combat.attack_range * 4  # Can detect enemies up to 4x attack range

        # Get all nearby enemies
        nearby_enemies = []
        for enemy in self.entity_manager.get_entities_with_tag(enemy_tag):
            if not enemy.active:
                continue

            enemy_health = enemy.get_component("Health")
            if enemy_health and enemy_health.dead:
                continue

            enemy_transform = enemy.get_component("Transform")
            if not enemy_transform:
                continue

            dx = enemy_transform.x - transform.x
            dy = enemy_transform.y - transform.y
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < detection_range:
                enemy_unit = enemy.get_component("Unit")
                rank = enemy_unit.rank if enemy_unit else "soldier"
                nearby_enemies.append((enemy, dist, rank, enemy_transform))

        if not nearby_enemies:
            return None, float('inf')

        # PRIORITY 1: Protect friendly commanders under threat
        # Check if our general is threatened
        generals = [e for e in self.entity_manager.get_entities_with_tag("general")
                   if e.active and e.has_tag(friendly_tag)]

        for general in generals:
            general_transform = general.get_component("Transform")
            if not general_transform:
                continue

            # Find enemies threatening our general
            for enemy, enemy_dist, enemy_rank, enemy_transform in nearby_enemies:
                dx = enemy_transform.x - general_transform.x
                dy = enemy_transform.y - general_transform.y
                threat_dist = math.sqrt(dx*dx + dy*dy)

                # Enemy within 200 pixels of our general = threat!
                if threat_dist < 200:
                    # Calculate distance from soldier to this threatening enemy
                    dx_soldier = enemy_transform.x - transform.x
                    dy_soldier = enemy_transform.y - transform.y
                    soldier_to_threat = math.sqrt(dx_soldier*dx_soldier + dy_soldier*dy_soldier)

                    print(f"[PROTECTION] Soldier protecting general from {enemy_rank}!")
                    return enemy, soldier_to_threat

        # Check if our officer is threatened (only check our squad's officer)
        squad_id = unit.squad_id if hasattr(unit, 'squad_id') else None
        if squad_id:
            squad_info = self.blackboard.get_squad_info(squad_id)
            if squad_info:
                officer_id = squad_info.get("officer_id")

                # Find our officer entity
                for entity in self.entity_manager.entities:
                    if entity.id == officer_id and entity.active:
                        officer_transform = entity.get_component("Transform")
                        if not officer_transform:
                            continue

                        # Find enemies threatening our officer
                        for enemy, enemy_dist, enemy_rank, enemy_transform in nearby_enemies:
                            dx = enemy_transform.x - officer_transform.x
                            dy = enemy_transform.y - officer_transform.y
                            threat_dist = math.sqrt(dx*dx + dy*dy)

                            # Enemy within 150 pixels of our officer = threat!
                            if threat_dist < 150:
                                dx_soldier = enemy_transform.x - transform.x
                                dy_soldier = enemy_transform.y - transform.y
                                soldier_to_threat = math.sqrt(dx_soldier*dx_soldier + dy_soldier*dy_soldier)

                                print(f"[PROTECTION] Soldier protecting officer from {enemy_rank}!")
                                return enemy, soldier_to_threat

        # PRIORITY 2: Target high-rank enemies
        # Rank priority scores: general=3, officer=2, soldier=1
        rank_scores = {"general": 3.0, "officer": 2.0, "soldier": 1.0}

        def target_score(enemy_tuple):
            enemy, dist, rank, _ = enemy_tuple
            rank_score = rank_scores.get(rank, 1.0)
            # Score = rank_value / (distance/100 + 0.5)
            # Prioritizes high rank, but distance still matters
            distance_factor = (dist / 100.0) + 0.5
            return rank_score / distance_factor

        # Sort by score (highest first)
        nearby_enemies.sort(key=target_score, reverse=True)

        best_enemy, best_dist, best_rank, _ = nearby_enemies[0]
        return best_enemy, best_dist

    def engage_enemy(self, transform, enemy, combat, dt):
        """Engage enemy in combat"""
        enemy_transform = enemy.get_component("Transform")
        if not enemy_transform:
            return

        dx = enemy_transform.x - transform.x
        dy = enemy_transform.y - transform.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > combat.attack_range:
            # Move closer
            if distance > 0:
                direction_x = dx / distance
                direction_y = dy / distance
                transform.vx = direction_x * 100
                transform.vy = direction_y * 100

                transform.x += transform.vx * dt
                transform.y += transform.vy * dt
        else:
            # In range - stop and attack (attack handled by combat system)
            transform.vx = 0
            transform.vy = 0

    def default_behavior(self, soldier_entity, transform, unit, combat, dt):
        """Default behavior when no officer commanding"""
        # Priority 1: Try to find ANY friendly officer or general to rally to
        team_tag = f"team_{unit.team}"

        # Look for officers first
        officers = [e for e in self.entity_manager.get_entities_with_tag("officer")
                   if e.active and e.has_tag(team_tag)]

        # If no officers, look for general
        if not officers:
            officers = [e for e in self.entity_manager.get_entities_with_tag("general")
                       if e.active and e.has_tag(team_tag)]

        # Rally to nearest commander
        if officers:
            nearest_officer = None
            nearest_officer_dist = float('inf')

            for officer in officers:
                off_transform = officer.get_component("Transform")
                if off_transform:
                    dx = off_transform.x - transform.x
                    dy = off_transform.y - transform.y
                    dist = math.sqrt(dx*dx + dy*dy)

                    if dist < nearest_officer_dist:
                        nearest_officer = off_transform
                        nearest_officer_dist = dist

            # Move toward commander if found
            if nearest_officer and nearest_officer_dist > 50:
                rally_speed = 100
                dx = nearest_officer.x - transform.x
                dy = nearest_officer.y - transform.y
                dist = math.sqrt(dx*dx + dy*dy)

                if dist > 0:
                    direction_x = dx / dist
                    direction_y = dy / dist
                    transform.vx = direction_x * rally_speed
                    transform.vy = direction_y * rally_speed
                    transform.x += transform.vx * dt
                    transform.y += transform.vy * dt
                print(f"[SOLDIER RALLY] Soldier moving to rally with commander at distance {int(nearest_officer_dist)}")
                return

        # Priority 2: Look for priority target to engage (with protection/rank priorities)
        nearest_enemy, nearest_dist = self.select_priority_target(
            soldier_entity, transform, unit, combat
        )

        if nearest_enemy and nearest_dist < 400:
            # Enemy nearby - engage
            self.engage_enemy(transform, nearest_enemy, combat, dt)
        else:
            # Priority 3: No commanders or enemies - defensive idle
            transform.vx = 0
            transform.vy = 0

    def scout_patrol_behavior(self, soldier_entity, transform, unit, combat, dt):
        """Scout patrols assigned position and reports enemy sightings"""
        # Get scout patrol position from blackboard
        patrol_pos = self.blackboard.get_scout_patrol_position(soldier_entity.id)

        if not patrol_pos:
            # No patrol position assigned - shouldn't happen, but default to rally behavior
            print(f"[SCOUT {soldier_entity.id}] WARNING: No patrol position assigned!")
            return

        patrol_x, patrol_y = patrol_pos

        # Calculate distance to patrol position
        dx = patrol_x - transform.x
        dy = patrol_y - transform.y
        distance_to_patrol = math.sqrt(dx*dx + dy*dy)

        # Look for nearby enemies to report
        enemy_team = 1 - unit.team
        enemy_tag = f"team_{enemy_team}"
        enemies = [e for e in self.entity_manager.get_entities_with_tag(enemy_tag)
                  if e.active]

        detection_range = 300  # Scouts can see enemies from 300 pixels away

        for enemy in enemies:
            enemy_health = enemy.get_component("Health")
            if enemy_health and enemy_health.dead:
                continue

            enemy_transform = enemy.get_component("Transform")
            enemy_unit = enemy.get_component("Unit")

            if enemy_transform:
                ex = enemy_transform.x - transform.x
                ey = enemy_transform.y - transform.y
                enemy_dist = math.sqrt(ex*ex + ey*ey)

                # Report enemy if within detection range
                if enemy_dist < detection_range:
                    enemy_type = enemy_unit.rank if enemy_unit else "unknown"
                    # Report to blackboard (will print to console)
                    self.blackboard.report_scout_sighting(
                        soldier_entity.id,
                        (enemy_transform.x, enemy_transform.y),
                        0,  # game_time (will be updated by system)
                        enemy_type
                    )

                    # Scouts don't engage - they avoid combat
                    if enemy_dist < combat.attack_range * 2:
                        # Enemy too close - retreat toward patrol position
                        if distance_to_patrol > 0:
                            retreat_speed = 140  # Scouts move faster when retreating
                            direction_x = dx / distance_to_patrol
                            direction_y = dy / distance_to_patrol
                            transform.vx = direction_x * retreat_speed
                            transform.vy = direction_y * retreat_speed
                            transform.x += transform.vx * dt
                            transform.y += transform.vy * dt
                        return

        # No immediate threats - patrol normally
        if distance_to_patrol > 20:
            # Move to patrol position
            patrol_speed = 100
            if distance_to_patrol > 0:
                direction_x = dx / distance_to_patrol
                direction_y = dy / distance_to_patrol
                transform.vx = direction_x * patrol_speed
                transform.vy = direction_y * patrol_speed
                transform.x += transform.vx * dt
                transform.y += transform.vy * dt
        else:
            # At patrol position - small circular patrol
            # Simple idle behavior - could be enhanced with actual patrol pattern
            transform.vx = 0
            transform.vy = 0


class SoldierAISystem:
    """System to update all soldier AI"""
    def __init__(self, entity_manager, blackboard, formation_manager):
        self.entity_manager = entity_manager
        self.blackboard = blackboard
        self.formation_manager = formation_manager
        self.soldier_ai = SoldierAI(entity_manager, blackboard, formation_manager)

    def update(self, dt):
        """Update all soldiers"""
        soldiers = self.entity_manager.get_entities_with_tag("soldier")

        for soldier in soldiers:
            if soldier.active:
                self.soldier_ai.update(dt, soldier)
