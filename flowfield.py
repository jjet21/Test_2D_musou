"""
Flow-field navigation system for efficient pathfinding of large enemy groups
"""
import numpy as np
from collections import deque


class FlowField:
    """
    Flow-field navigation grid.
    Each cell stores a direction vector toward the nearest target.
    """
    def __init__(self, world_width, world_height, cell_size=32):
        self.world_width = world_width
        self.world_height = world_height
        self.cell_size = cell_size

        # Grid dimensions
        self.grid_width = world_width // cell_size
        self.grid_height = world_height // cell_size

        # Flow field: direction vectors for each cell
        self.flow = np.zeros((self.grid_height, self.grid_width, 2), dtype=np.float32)

        # Cost field: navigation cost for each cell (0 = normal, higher = obstacle)
        self.cost_field = np.ones((self.grid_height, self.grid_width), dtype=np.float32)

        # Integration field: distance to goal
        self.integration_field = np.full((self.grid_height, self.grid_width), np.inf, dtype=np.float32)

        # Targets (goal positions)
        self.targets = []

        # Update throttling
        self.update_cooldown = 0.5  # Update every 0.5 seconds
        self.update_timer = 0

    def set_cost(self, x, y, cost):
        """Set navigation cost for a cell"""
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            self.cost_field[grid_y, grid_x] = cost

    def add_target(self, x, y):
        """Add a target position (goal)"""
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            self.targets.append((grid_x, grid_y))

    def clear_targets(self):
        """Clear all targets"""
        self.targets.clear()

    def update(self, dt):
        """Update flow field (throttled)"""
        self.update_timer += dt
        if self.update_timer >= self.update_cooldown:
            self.update_timer = 0
            if self.targets:
                self.generate_flow_field()

    def generate_flow_field(self):
        """Generate flow field using Dijkstra-like algorithm"""
        # Reset integration field
        self.integration_field.fill(np.inf)

        # BFS queue
        queue = deque()

        # Initialize targets with 0 cost
        for target in self.targets:
            gx, gy = target
            self.integration_field[gy, gx] = 0
            queue.append((gx, gy))

        # Dijkstra's algorithm to calculate integration field
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal
                     (1, 1), (1, -1), (-1, 1), (-1, -1)]  # Diagonal

        while queue:
            cx, cy = queue.popleft()
            current_cost = self.integration_field[cy, cx]

            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy

                # Check bounds
                if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    continue

                # Calculate new cost
                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0  # Diagonal vs cardinal
                new_cost = current_cost + move_cost * self.cost_field[ny, nx]

                # Update if we found a better path
                if new_cost < self.integration_field[ny, nx]:
                    self.integration_field[ny, nx] = new_cost
                    queue.append((nx, ny))

        # Generate flow field from integration field
        self.generate_flow_vectors()

    def generate_flow_vectors(self):
        """Generate flow vectors from integration field"""
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
        ]

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if np.isinf(self.integration_field[y, x]):
                    self.flow[y, x] = [0, 0]
                    continue

                # Find direction to lowest cost neighbor
                best_cost = self.integration_field[y, x]
                best_dir = np.array([0.0, 0.0])

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        if self.integration_field[ny, nx] < best_cost:
                            best_cost = self.integration_field[ny, nx]
                            best_dir = np.array([dx, dy], dtype=np.float32)

                # Normalize
                if np.linalg.norm(best_dir) > 0:
                    best_dir = best_dir / np.linalg.norm(best_dir)

                self.flow[y, x] = best_dir

    def get_direction(self, x, y):
        """Get flow direction at world position"""
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)

        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.flow[grid_y, grid_x]
        return np.array([0.0, 0.0])

    def get_cell_center(self, grid_x, grid_y):
        """Get world position of cell center"""
        return (grid_x * self.cell_size + self.cell_size // 2,
                grid_y * self.cell_size + self.cell_size // 2)

    def draw_debug(self, surface, camera_offset=(0, 0)):
        """Draw flow field for debugging"""
        import pygame
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Skip cells with no flow
                if np.linalg.norm(self.flow[y, x]) < 0.01:
                    continue

                # Get cell center in world space
                cx, cy = self.get_cell_center(x, y)

                # Apply camera offset
                screen_x = cx - camera_offset[0]
                screen_y = cy - camera_offset[1]

                # Draw arrow
                direction = self.flow[y, x]
                end_x = screen_x + direction[0] * self.cell_size * 0.3
                end_y = screen_y + direction[1] * self.cell_size * 0.3

                pygame.draw.line(surface, (100, 255, 100),
                               (screen_x, screen_y), (end_x, end_y), 1)
