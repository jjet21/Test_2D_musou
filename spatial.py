"""
Spatial hashing system for efficient collision detection
"""
import math


class SpatialHash:
    """
    Spatial hashing grid for broad-phase collision detection.
    Divides world into cells and tracks which entities are in each cell.
    """
    def __init__(self, cell_size=100):
        self.cell_size = cell_size
        self.grid = {}  # Dictionary of cell_key -> list of entities

    def _get_cell_key(self, x, y):
        """Get cell key for a position"""
        cell_x = int(x // self.cell_size)
        cell_y = int(y // self.cell_size)
        return (cell_x, cell_y)

    def _get_cells_for_bounds(self, x, y, radius):
        """Get all cell keys that a bounded object touches"""
        min_x = x - radius
        max_x = x + radius
        min_y = y - radius
        max_y = y + radius

        min_cell_x = int(min_x // self.cell_size)
        max_cell_x = int(max_x // self.cell_size)
        min_cell_y = int(min_y // self.cell_size)
        max_cell_y = int(max_y // self.cell_size)

        cells = []
        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cells.append((cx, cy))
        return cells

    def insert(self, entity, x, y, radius=0):
        """Insert entity into spatial hash"""
        if radius > 0:
            cells = self._get_cells_for_bounds(x, y, radius)
        else:
            cells = [self._get_cell_key(x, y)]

        for cell in cells:
            if cell not in self.grid:
                self.grid[cell] = []
            if entity not in self.grid[cell]:
                self.grid[cell].append(entity)

    def remove(self, entity, x, y, radius=0):
        """Remove entity from spatial hash"""
        if radius > 0:
            cells = self._get_cells_for_bounds(x, y, radius)
        else:
            cells = [self._get_cell_key(x, y)]

        for cell in cells:
            if cell in self.grid and entity in self.grid[cell]:
                self.grid[cell].remove(entity)
                if not self.grid[cell]:
                    del self.grid[cell]

    def query_radius(self, x, y, radius):
        """Query all entities within radius of a point"""
        cells = self._get_cells_for_bounds(x, y, radius)
        entities = set()

        for cell in cells:
            if cell in self.grid:
                entities.update(self.grid[cell])

        # Narrow phase: check actual distance
        results = []
        radius_sq = radius * radius

        for entity in entities:
            transform = entity.get_component("Transform")
            if transform:
                dx = transform.x - x
                dy = transform.y - y
                dist_sq = dx*dx + dy*dy
                if dist_sq <= radius_sq:
                    results.append(entity)

        return results

    def query_rect(self, x, y, width, height):
        """Query all entities within a rectangle"""
        min_x, max_x = x, x + width
        min_y, max_y = y, y + height

        min_cell_x = int(min_x // self.cell_size)
        max_cell_x = int(max_x // self.cell_size)
        min_cell_y = int(min_y // self.cell_size)
        max_cell_y = int(max_y // self.cell_size)

        entities = set()
        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cell = (cx, cy)
                if cell in self.grid:
                    entities.update(self.grid[cell])

        return list(entities)

    def clear(self):
        """Clear all entities from spatial hash"""
        self.grid.clear()

    def rebuild(self, entities):
        """Rebuild spatial hash from entity list"""
        self.clear()
        for entity in entities:
            if entity.active:
                # Skip dead entities from spatial hash
                health = entity.get_component("Health")
                if health and health.dead:
                    continue

                transform = entity.get_component("Transform")
                if transform:
                    sprite = entity.get_component("Sprite")
                    radius = max(sprite.width, sprite.height) // 2 if sprite else 0
                    self.insert(entity, transform.x, transform.y, radius)


class CollisionSystem:
    """System for handling collisions using spatial hashing"""
    def __init__(self, entity_manager, cell_size=100):
        self.entity_manager = entity_manager
        self.spatial_hash = SpatialHash(cell_size)

    def update(self, dt):
        """Update spatial hash and check collisions"""
        # Rebuild spatial hash each frame
        self.spatial_hash.rebuild(self.entity_manager.entities)

    def check_attack_collisions(self, x, y, radius, damage, attacker_team):
        """Check for entities hit by an attack (does NOT apply damage, just returns targets)"""
        entities = self.spatial_hash.query_radius(x, y, radius)
        hits = []

        for entity in entities:
            combat = entity.get_component("Combat")
            health = entity.get_component("Health")

            # Check if entity can be hit (but don't apply damage here!)
            if combat and health and combat.team != attacker_team:
                if not health.dead:
                    hits.append(entity)

        return hits

    def check_entity_collisions(self, entity, radius):
        """Check for collisions with other entities"""
        transform = entity.get_component("Transform")
        if not transform:
            return []

        return self.spatial_hash.query_radius(transform.x, transform.y, radius)
