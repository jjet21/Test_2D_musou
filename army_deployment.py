"""
Army deployment system
Sets up initial armies on both sides of the map
"""
from game.army_units import create_soldier, create_officer, create_general
from game.formation import FormationType
import random


class ArmyDeployment:
    """
    Handles initial deployment of armies and ongoing reinforcements.
    """
    def __init__(self, entity_manager, blackboard, formation_manager):
        self.entity_manager = entity_manager
        self.blackboard = blackboard
        self.formation_manager = formation_manager

        # Reinforcement system
        self.reinforcement_interval = 120.0  # 2 minutes
        self.reinforcement_timer = 0.0
        self.reinforcements_per_wave = 5

    def deploy_armies(self, world_width, world_height):
        """
        Deploy initial armies on both sides of map.
        Player army (team 0) on left, Enemy army (team 1) on right.
        """
        # Player army (left side)
        self.deploy_team_army(
            team_id=0,
            base_x=400,
            center_y=world_height // 2,
            num_officers=3,
            soldiers_per_squad=10
        )

        # Enemy army (right side)
        self.deploy_team_army(
            team_id=1,
            base_x=world_width - 400,
            center_y=world_height // 2,
            num_officers=3,
            soldiers_per_squad=10
        )

    def deploy_team_army(self, team_id, base_x, center_y, num_officers=3, soldiers_per_squad=10):
        """
        Deploy one team's army.

        Args:
            team_id: 0 for player team, 1 for enemy team
            base_x: X position for deployment line
            center_y: Center Y of deployment
            num_officers: Number of officer squads
            soldiers_per_squad: Soldiers per officer
        """
        # Create general with correct team
        general = create_general(self.entity_manager, base_x, center_y, team=team_id)
        print(f"[DEPLOYMENT] Created General {general.id} for team {team_id} at ({base_x}, {center_y})")

        # Create officers in line formation
        officer_spacing = 400  # Vertical spacing between officer squads
        start_y = center_y - (num_officers - 1) * officer_spacing / 2

        officers = []
        for i in range(num_officers):
            officer_y = start_y + i * officer_spacing
            officer = create_officer(self.entity_manager, base_x, officer_y, team=team_id)

            # Register squad with blackboard
            squad_id = f"team{team_id}_squad{i}"
            self.blackboard.register_squad(squad_id, officer.id, formation="line")

            # Assign officer to squad
            unit = officer.get_component("Unit")
            if unit:
                unit.squad_id = squad_id

            # Create formation for squad
            self.formation_manager.create_formation(squad_id, FormationType.LINE, looseness=0.3)

            officers.append((officer, squad_id, officer_y))
            print(f"[DEPLOYMENT] Created Officer {officer.id} for squad {squad_id}")

        # Deploy soldiers for each officer
        for officer, squad_id, officer_y in officers:
            self.deploy_squad_soldiers(
                team_id, squad_id, base_x, officer_y, soldiers_per_squad
            )

    def deploy_squad_soldiers(self, team_id, squad_id, base_x, base_y, count):
        """Deploy soldiers for a squad in line formation"""
        soldier_spacing = 50
        start_x = base_x - (count - 1) * soldier_spacing / 2

        for i in range(count):
            soldier_x = start_x + i * soldier_spacing
            soldier_y = base_y + random.uniform(-20, 20)  # Slight Y variance

            soldier = create_soldier(self.entity_manager, soldier_x, soldier_y, team=team_id)

            # Assign to squad
            self.blackboard.add_soldier_to_squad(squad_id, soldier.id)

            unit = soldier.get_component("Unit")
            if unit:
                unit.squad_id = squad_id

        print(f"[DEPLOYMENT] Deployed {count} soldiers to {squad_id}")

    def update(self, dt):
        """Update reinforcement timer"""
        self.reinforcement_timer += dt

        if self.reinforcement_timer >= self.reinforcement_interval:
            self.reinforcement_timer = 0.0
            self.spawn_reinforcements()

    def spawn_reinforcements(self):
        """Spawn reinforcement wave for both teams"""
        print("[REINFORCEMENTS] Spawning reinforcement wave...")

        # Spawn for team 0
        self.spawn_team_reinforcements(0)

        # Spawn for team 1
        self.spawn_team_reinforcements(1)

    def spawn_team_reinforcements(self, team_id):
        """Spawn reinforcements for one team"""
        # Find all squads for this team
        team_squads = []
        for squad_id, squad_data in self.blackboard.squad_assignments.items():
            if squad_id.startswith(f"team{team_id}"):
                current_size = len(squad_data["soldier_ids"])
                max_size = squad_data["max_size"]
                if current_size < max_size:
                    team_squads.append((squad_id, current_size, max_size))

        if not team_squads:
            return

        # Sort by most depleted (lowest percentage of max)
        team_squads.sort(key=lambda x: x[1] / x[2] if x[2] > 0 else 0)

        # Distribute reinforcements
        reinforcements_left = self.reinforcements_per_wave

        for squad_id, current_size, max_size in team_squads:
            if reinforcements_left <= 0:
                break

            # How many can this squad receive?
            capacity = max_size - current_size
            to_spawn = min(capacity, reinforcements_left)

            # Find officer position for this squad
            squad_data = self.blackboard.squad_assignments[squad_id]
            officer_id = squad_data["officer_id"]

            officer_entity = None
            for e in self.entity_manager.entities:
                if e.id == officer_id:
                    officer_entity = e
                    break

            if officer_entity:
                officer_transform = officer_entity.get_component("Transform")
                if officer_transform:
                    # Spawn soldiers near officer
                    for i in range(to_spawn):
                        spawn_x = officer_transform.x + random.uniform(-100, 100)
                        spawn_y = officer_transform.y + random.uniform(-100, 100)

                        soldier = create_soldier(self.entity_manager, spawn_x, spawn_y, team=team_id)

                        # Assign to squad
                        self.blackboard.add_soldier_to_squad(squad_id, soldier.id)

                        unit = soldier.get_component("Unit")
                        if unit:
                            unit.squad_id = squad_id

                    reinforcements_left -= to_spawn
                    print(f"[REINFORCEMENTS] Spawned {to_spawn} soldiers for {squad_id}")

    def setup_base_priorities(self, objective_system):
        """Set strategic values for bases"""
        for base in objective_system.bases:
            if "center" in base.name.lower() or "central" in base.name.lower():
                # Center base is high value
                priority = 1.5
            else:
                priority = 1.0

            # Store in blackboard (both generals can read)
            # This would typically be done in GeneralAI, but we set defaults here
            print(f"[DEPLOYMENT] Base '{base.name}' priority: {priority}x")
