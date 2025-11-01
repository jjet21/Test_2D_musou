"""
Object pooling system for performance optimization
Reduces GC pressure by reusing objects instead of creating/destroying them
"""


class ObjectPool:
    """Generic object pool"""
    def __init__(self, factory_func, initial_size=100):
        """
        Args:
            factory_func: Function that creates new objects
            initial_size: Number of objects to pre-allocate
        """
        self.factory_func = factory_func
        self.available = []
        self.in_use = []

        # Pre-allocate objects
        for _ in range(initial_size):
            obj = factory_func()
            self.available.append(obj)

    def acquire(self):
        """Get an object from the pool"""
        if self.available:
            obj = self.available.pop()
            self.in_use.append(obj)
            return obj
        else:
            # Pool exhausted, create new object
            obj = self.factory_func()
            self.in_use.append(obj)
            return obj

    def release(self, obj):
        """Return an object to the pool"""
        if obj in self.in_use:
            self.in_use.remove(obj)
            self.available.append(obj)

            # Reset object if it has a reset method
            if hasattr(obj, 'reset'):
                obj.reset()

    def release_all(self):
        """Return all in-use objects to the pool"""
        self.available.extend(self.in_use)
        self.in_use.clear()

        # Reset all objects
        for obj in self.available:
            if hasattr(obj, 'reset'):
                obj.reset()

    def get_stats(self):
        """Get pool statistics"""
        return {
            'available': len(self.available),
            'in_use': len(self.in_use),
            'total': len(self.available) + len(self.in_use)
        }


class EntityPool:
    """Specialized pool for entities"""
    def __init__(self, entity_manager, entity_factory_func, initial_size=100):
        """
        Args:
            entity_manager: EntityManager instance
            entity_factory_func: Function that creates and configures an entity
            initial_size: Number of entities to pre-allocate
        """
        self.entity_manager = entity_manager
        self.factory_func = entity_factory_func
        self.available = []
        self.in_use = []

        # Pre-allocate entities
        for _ in range(initial_size):
            entity = entity_factory_func(entity_manager)
            entity.active = False  # Start inactive
            self.available.append(entity)

    def acquire(self):
        """Get an entity from the pool"""
        if self.available:
            entity = self.available.pop()
            entity.active = True
            self.in_use.append(entity)
            # Debug: Disabled excessive logging
            # print(f"[POOL] Acquired entity {entity.id} from pool")
            return entity
        else:
            # Pool exhausted, create new entity
            entity = self.factory_func(self.entity_manager)
            entity.active = True
            self.in_use.append(entity)
            print(f"[POOL] WARNING: Pool exhausted, created NEW entity {entity.id}")
            return entity

    def release(self, entity):
        """Return an entity to the pool"""
        # Debug: Disabled excessive logging and stack traces
        # print(f"[POOL] Releasing entity {entity.id}")

        if entity in self.in_use:
            self.in_use.remove(entity)
            self.available.append(entity)

            # Deactivate and reset
            entity.active = False

            # Reset all components
            for component in entity.components.values():
                if hasattr(component, 'reset'):
                    component.reset()
        else:
            print(f"[POOL] WARNING: Entity {entity.id} not in in_use list - possible double release!")

    def release_all(self):
        """Return all in-use entities to the pool"""
        for entity in self.in_use:
            entity.active = False
            for component in entity.components.values():
                if hasattr(component, 'reset'):
                    component.reset()

        self.available.extend(self.in_use)
        self.in_use.clear()

    def get_stats(self):
        """Get pool statistics"""
        return {
            'available': len(self.available),
            'in_use': len(self.in_use),
            'total': len(self.available) + len(self.in_use)
        }


class PoolManager:
    """Manages multiple object pools"""
    def __init__(self):
        self.pools = {}

    def create_pool(self, name, factory_func, initial_size=100):
        """Create a new pool"""
        self.pools[name] = ObjectPool(factory_func, initial_size)

    def create_entity_pool(self, name, entity_manager, factory_func, initial_size=100):
        """Create a new entity pool"""
        self.pools[name] = EntityPool(entity_manager, factory_func, initial_size)

    def acquire(self, pool_name):
        """Acquire object from a pool"""
        if pool_name in self.pools:
            return self.pools[pool_name].acquire()
        return None

    def release(self, pool_name, obj):
        """Release object back to a pool"""
        if pool_name in self.pools:
            self.pools[pool_name].release(obj)

    def get_stats(self):
        """Get statistics for all pools"""
        return {name: pool.get_stats() for name, pool in self.pools.items()}
