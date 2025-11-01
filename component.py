"""
Component base class for Entity-Component System
"""

class Component:
    """Base component class"""
    def __init__(self):
        self.entity = None

    def update(self, dt):
        """Override in subclasses"""
        pass


class Transform(Component):
    """Position, rotation, scale component"""
    def __init__(self, x=0, y=0, rotation=0):
        super().__init__()
        self.x = x
        self.y = y
        self.rotation = rotation
        self.vx = 0  # velocity
        self.vy = 0

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, value):
        self.x, self.y = value

    def reset(self):
        """Reset transform to default state"""
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.rotation = 0


class Sprite(Component):
    """Rendering component"""
    def __init__(self, surface, width=32, height=32):
        super().__init__()
        self.surface = surface
        self.width = width
        self.height = height
        self.visible = True
        self.layer = 0  # For sorting

    def get_rect(self):
        """Get rect for the sprite based on entity transform"""
        if self.entity and 'Transform' in self.entity.components:
            transform = self.entity.components['Transform']
            return (transform.x - self.width // 2,
                   transform.y - self.height // 2,
                   self.width, self.height)
        return (0, 0, self.width, self.height)

    def reset(self):
        """Reset sprite to default state"""
        self.visible = True
        # Don't reset layer - it's a property of the sprite type, not state


class Health(Component):
    """Health/damage component"""
    def __init__(self, max_health=100):
        super().__init__()
        self.max_health = max_health
        self.current_health = max_health
        self.invulnerable = False
        self.dead = False

    def take_damage(self, amount):
        """Apply damage"""
        if not self.invulnerable and not self.dead:
            self.current_health -= amount
            if self.current_health <= 0:
                self.current_health = 0
                self.dead = True
                return True
        return False

    def heal(self, amount):
        """Heal"""
        self.current_health = min(self.max_health, self.current_health + amount)

    @property
    def health_percent(self):
        return self.current_health / self.max_health if self.max_health > 0 else 0

    def reset(self):
        """Reset health to default state"""
        self.current_health = self.max_health
        self.dead = False
        self.invulnerable = False


class Combat(Component):
    """Combat stats component"""
    def __init__(self, damage=10, attack_range=50, attack_cooldown=1.0):
        super().__init__()
        self.damage = damage
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self.cooldown_timer = 0
        self.team = 0  # 0 = player, 1 = enemy

    def update(self, dt):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    def can_attack(self):
        return self.cooldown_timer <= 0

    def attack(self):
        """Trigger attack cooldown"""
        self.cooldown_timer = self.attack_cooldown


class AI(Component):
    """AI state machine component"""
    def __init__(self, initial_state="idle"):
        super().__init__()
        self.state = initial_state
        self.target = None
        self.state_timer = 0
        self.decision_cooldown = 0.5
        self.decision_timer = 0

    def update(self, dt):
        self.state_timer += dt
        self.decision_timer += dt

    def can_make_decision(self):
        return self.decision_timer >= self.decision_cooldown

    def reset_decision_timer(self):
        self.decision_timer = 0

    def change_state(self, new_state):
        self.state = new_state
        self.state_timer = 0
