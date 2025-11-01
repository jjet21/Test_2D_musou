"""
Entity class for Entity-Component System
"""

class Entity:
    """Entity that holds components"""
    _next_id = 0

    def __init__(self):
        self.id = Entity._next_id
        Entity._next_id += 1
        self.components = {}
        self.active = True
        self.tags = set()

    def add_component(self, component_name, component):
        """Add a component to this entity"""
        self.components[component_name] = component
        component.entity = self
        return self

    def get_component(self, component_name):
        """Get a component by name"""
        return self.components.get(component_name)

    def has_component(self, component_name):
        """Check if entity has a component"""
        return component_name in self.components

    def remove_component(self, component_name):
        """Remove a component"""
        if component_name in self.components:
            del self.components[component_name]

    def add_tag(self, tag):
        """Add a tag to this entity"""
        self.tags.add(tag)

    def has_tag(self, tag):
        """Check if entity has a tag"""
        return tag in self.tags

    def destroy(self):
        """Mark entity for destruction"""
        if self.has_tag("enemy"):
            import traceback
            print(f"[ENTITY] destroy() called on enemy {self.id}!")
            traceback.print_stack(limit=5)
        self.active = False


class EntityManager:
    """Manages all entities"""
    def __init__(self):
        self.entities = []
        self.entities_by_tag = {}

    def create_entity(self):
        """Create a new entity"""
        entity = Entity()
        self.entities.append(entity)
        return entity

    def destroy_entity(self, entity):
        """Destroy an entity"""
        entity.destroy()

    def get_entities_with_component(self, component_name):
        """Get all entities that have a specific component"""
        return [e for e in self.entities if e.active and e.has_component(component_name)]

    def get_entities_with_tag(self, tag):
        """Get all entities with a specific tag"""
        return [e for e in self.entities if e.active and e.has_tag(tag)]

    def update(self, dt):
        """Update all entity components"""
        for entity in self.entities:
            if entity.active:
                for component in entity.components.values():
                    # Only update components that have an update method
                    if hasattr(component, 'update') and callable(component.update):
                        try:
                            component.update(dt)
                        except Exception as e:
                            print(f"Error in entity_manager.update for component {type(component).__name__}: {e}")

    def cleanup(self):
        """Remove inactive entities (except pooled ones)

        Note: When using object pooling, inactive entities should stay in the list
        so they can be reactivated. Only remove entities that don't have pool-related tags.
        """
        # Don't remove enemies - they're managed by the pool
        # Only remove non-pooled entities like temporary attacks
        self.entities = [e for e in self.entities if e.active or e.has_tag("enemy")]

    def clear(self):
        """Clear all entities"""
        self.entities.clear()
        self.entities_by_tag.clear()
