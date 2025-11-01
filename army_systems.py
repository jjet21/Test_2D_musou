"""
Army systems integration
Coordinates all army AI layers (General → Officer → Soldier)
"""
from game.blackboard import BattlefieldBlackboard
from game.formation import FormationManager
from game.army_ai import GeneralAI, OfficerAI
from game.army_soldier_ai import SoldierAISystem
from game.army_deployment import ArmyDeployment


class ArmyManager:
    """
    Central coordinator for entire army system.
    Manages generals, officers, soldiers, formations, and deployment.
    """
    def __init__(self, entity_manager, objective_system):
        self.entity_manager = entity_manager
        self.objective_system = objective_system

        # Core systems
        self.blackboard = BattlefieldBlackboard()
        self.formation_manager = FormationManager()
        self.deployment = ArmyDeployment(entity_manager, self.blackboard, self.formation_manager)

        # AI controllers
        self.general_ai_team0 = GeneralAI(0, self.blackboard, self.formation_manager)
        self.general_ai_team1 = GeneralAI(1, self.blackboard, self.formation_manager)

        self.officer_ais = {}  # officer_id -> OfficerAI instance
        self.soldier_ai_system = SoldierAISystem(entity_manager, self.blackboard, self.formation_manager)

        # Setup complete flag
        self.armies_deployed = False

        # Game time (for command delays)
        self.game_time = 0.0

    def initialize_armies(self, world_width, world_height):
        """Deploy initial armies"""
        if not self.armies_deployed:
            self.deployment.deploy_armies(world_width, world_height)
            self.deployment.setup_base_priorities(self.objective_system)

            # Set center base as high priority
            self.general_ai_team0.set_objective_priority("Center Base", 1.5)
            self.general_ai_team1.set_objective_priority("Center Base", 1.5)

            self.armies_deployed = True
            print("[ARMY_MANAGER] Armies deployed successfully")

    def update(self, dt):
        """Update all army systems"""
        self.game_time += dt

        # Update blackboard command delays
        self._process_delayed_orders()

        # Update reinforcements
        self.deployment.update(dt)

        # Update General AI (strategic layer)
        self._update_generals(dt)

        # Update Officer AI (tactical layer)
        self._update_officers(dt)

        # Update Soldier AI (individual layer)
        self.soldier_ai_system.update(dt)

        # Update squad cohesion metrics
        self._update_squad_cohesion()

        # Update team morale
        self._update_morale(dt)

    def _update_generals(self, dt):
        """Update both team generals"""
        # Find generals
        general_team0 = None
        general_team1 = None

        for entity in self.entity_manager.get_entities_with_tag("general"):
            if not entity.active:
                continue

            unit = entity.get_component("Unit")
            if unit:
                if unit.team == 0:
                    general_team0 = entity
                elif unit.team == 1:
                    general_team1 = entity

        # Update team 0 general
        if general_team0:
            self.general_ai_team0.update(dt, self.entity_manager, general_team0, self.objective_system, self.game_time)

        # Update team 1 general
        if general_team1:
            self.general_ai_team1.update(dt, self.entity_manager, general_team1, self.objective_system, self.game_time)

    def _update_officers(self, dt):
        """Update all officers"""
        officers = self.entity_manager.get_entities_with_tag("officer")

        for officer in officers:
            if not officer.active:
                continue

            unit = officer.get_component("Unit")
            if not unit or not unit.squad_id:
                continue

            # Get or create OfficerAI for this officer
            if officer.id not in self.officer_ais:
                self.officer_ais[officer.id] = OfficerAI(
                    unit.squad_id, self.blackboard, self.formation_manager, self.entity_manager
                )

            officer_ai = self.officer_ais[officer.id]
            officer_ai.update(dt, self.entity_manager, officer, self.game_time, self.objective_system)

    def _update_squad_cohesion(self):
        """Calculate cohesion for all squads"""
        for squad_id, squad_data in self.blackboard.squad_assignments.items():
            soldier_ids = squad_data["soldier_ids"]

            # Get actual positions of soldiers
            soldier_positions = []
            for soldier_id in soldier_ids:
                soldier = None
                for e in self.entity_manager.entities:
                    if e.id == soldier_id and e.active:
                        soldier = e
                        break

                if soldier:
                    transform = soldier.get_component("Transform")
                    if transform:
                        soldier_positions.append((transform.x, transform.y))

            # Update cohesion
            if soldier_positions:
                cohesion = self.formation_manager.update_cohesion(squad_id, soldier_positions)
                self.blackboard.update_cohesion(squad_id, cohesion)

    def _update_morale(self, dt):
        """Update team morale based on battlefield conditions"""
        for team_id in [0, 1]:
            stats = self.blackboard.get_team_stats(team_id)

            # Morale factors
            morale_delta = 0.0

            # Casualties reduce morale
            if stats["casualties"] > 0:
                morale_delta -= 0.01 * dt

            # Having more units than enemy increases morale
            enemy_team = 1 - team_id
            enemy_stats = self.blackboard.get_team_stats(enemy_team)

            if stats["total_units"] > enemy_stats["total_units"]:
                morale_delta += 0.005 * dt
            else:
                morale_delta -= 0.005 * dt

            # Owning bases increases morale
            if team_id == 0:
                our_bases = len(self.objective_system.get_player_bases())
                enemy_bases = len(self.objective_system.get_enemy_bases())
            else:
                our_bases = len(self.objective_system.get_enemy_bases())
                enemy_bases = len(self.objective_system.get_player_bases())

            if our_bases > enemy_bases:
                morale_delta += 0.01 * dt
            elif enemy_bases > our_bases:
                morale_delta -= 0.01 * dt

            # Apply morale change
            self.blackboard.update_morale(team_id, morale_delta)

    def _process_delayed_orders(self):
        """Process pending orders in blackboard (command delay system)"""
        # This is handled internally by blackboard.get_orders_for_unit()
        # which checks game_time against order delivery times
        pass

    def draw_debug(self, screen, camera_x, camera_y):
        """Draw debug visualization (command radii, formations)"""
        import pygame
        from game.formation import CommandInfluence

        # Draw command influence radii
        for entity in self.entity_manager.entities:
            if not entity.active:
                continue

            if entity.has_tag("officer") or entity.has_tag("general"):
                transform = entity.get_component("Transform")
                unit = entity.get_component("Unit")

                if transform and unit:
                    screen_x = int(transform.x - camera_x)
                    screen_y = int(transform.y - camera_y)

                    # Get radius
                    radius = CommandInfluence.INFLUENCE_RADIUS.get(unit.rank, 300)

                    # Draw subtle aura
                    color = (100, 150, 255, 30) if unit.team == 0 else (255, 100, 100, 30)

                    # Create transparent surface for aura
                    aura_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(aura_surface, color, (radius, radius), radius, 2)

                    screen.blit(aura_surface, (screen_x - radius, screen_y - radius))

        # Draw formation positions (debug lines)
        for squad_id in self.formation_manager.formations.keys():
            squad_data = self.blackboard.get_squad_info(squad_id)
            if not squad_data:
                continue

            soldier_ids = squad_data["soldier_ids"]
            formation_positions = self.formation_manager.get_formation_positions(
                squad_id, len(soldier_ids)
            )

            # Draw small circles at formation positions
            for fx, fy in formation_positions:
                screen_x = int(fx - camera_x)
                screen_y = int(fy - camera_y)
                pygame.draw.circle(screen, (255, 255, 0), (screen_x, screen_y), 3, 1)

    def get_stats_for_ui(self):
        """Get army statistics for UI display"""
        return {
            "team0": self.blackboard.get_team_stats(0),
            "team1": self.blackboard.get_team_stats(1),
            "morale_team0": self.blackboard.get_morale(0),
            "morale_team1": self.blackboard.get_morale(1)
        }
