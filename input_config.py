"""
Keyboard configuration system for multiple layouts
Supports QWERTY, AZERTY, QWERTZ, and custom keybinds
"""
import pygame
import json
import os
import locale


class KeyBindings:
    """Manages key bindings for different keyboard layouts"""

    # Preset layouts
    LAYOUTS = {
        "QWERTY": {
            "move_up": [pygame.K_w, pygame.K_UP],
            "move_down": [pygame.K_s, pygame.K_DOWN],
            "move_left": [pygame.K_a, pygame.K_LEFT],
            "move_right": [pygame.K_d, pygame.K_RIGHT],
            "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "light_attack": [pygame.K_SPACE],
            "heavy_attack": [pygame.K_LCTRL, pygame.K_RCTRL],
            "musou_attack": [pygame.K_m],
        },
        "AZERTY": {
            "move_up": [pygame.K_z, pygame.K_UP],
            "move_down": [pygame.K_s, pygame.K_DOWN],
            "move_left": [pygame.K_q, pygame.K_LEFT],
            "move_right": [pygame.K_d, pygame.K_RIGHT],
            "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "light_attack": [pygame.K_SPACE],
            "heavy_attack": [pygame.K_LCTRL, pygame.K_RCTRL],
            "musou_attack": [pygame.K_m],
        },
        "QWERTZ": {
            "move_up": [pygame.K_w, pygame.K_UP],
            "move_down": [pygame.K_s, pygame.K_DOWN],
            "move_left": [pygame.K_a, pygame.K_LEFT],
            "move_right": [pygame.K_d, pygame.K_RIGHT],
            "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "light_attack": [pygame.K_SPACE],
            "heavy_attack": [pygame.K_LCTRL, pygame.K_RCTRL],
            "musou_attack": [pygame.K_m],
        },
        "ARROWS": {
            "move_up": [pygame.K_UP],
            "move_down": [pygame.K_DOWN],
            "move_left": [pygame.K_LEFT],
            "move_right": [pygame.K_RIGHT],
            "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "light_attack": [pygame.K_SPACE, pygame.K_z],
            "heavy_attack": [pygame.K_x],
            "musou_attack": [pygame.K_c],
        },
        "IJKL": {
            "move_up": [pygame.K_i, pygame.K_UP],
            "move_down": [pygame.K_k, pygame.K_DOWN],
            "move_left": [pygame.K_j, pygame.K_LEFT],
            "move_right": [pygame.K_l, pygame.K_RIGHT],
            "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "light_attack": [pygame.K_SPACE],
            "heavy_attack": [pygame.K_u],
            "musou_attack": [pygame.K_o],
        },
    }

    def __init__(self, layout="QWERTY", config_file="config/keybinds.json"):
        self.config_file = config_file
        self.current_layout = layout
        self.bindings = {}

        # Load or create default bindings
        self.load_bindings()

    def load_bindings(self):
        """Load keybindings from file or use default layout"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.current_layout = data.get('layout', 'QWERTY')
                    self.bindings = self._convert_keys_from_json(data.get('bindings', {}))
                    print(f"Loaded keybindings: {self.current_layout} layout")
                    return
            except Exception as e:
                print(f"Error loading keybindings: {e}")

        # Use default layout
        self.set_layout(self.current_layout)

    def save_bindings(self):
        """Save current keybindings to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            data = {
                'layout': self.current_layout,
                'bindings': self._convert_keys_to_json(self.bindings)
            }

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved keybindings: {self.current_layout} layout")
        except Exception as e:
            print(f"Error saving keybindings: {e}")

    def set_layout(self, layout_name):
        """Set keyboard layout from presets"""
        if layout_name in self.LAYOUTS:
            self.current_layout = layout_name
            self.bindings = self.LAYOUTS[layout_name].copy()
            self.save_bindings()
            return True
        return False

    def get_available_layouts(self):
        """Get list of available preset layouts"""
        return list(self.LAYOUTS.keys())

    def is_key_pressed(self, action, keys_pressed):
        """Check if any key for an action is pressed"""
        if action in self.bindings:
            for key in self.bindings[action]:
                if keys_pressed[key]:
                    return True
        return False

    def bind_key(self, action, key):
        """Add a key binding for an action"""
        if action not in self.bindings:
            self.bindings[action] = []
        if key not in self.bindings[action]:
            self.bindings[action].append(key)
            self.current_layout = "CUSTOM"
            self.save_bindings()

    def unbind_key(self, action, key):
        """Remove a key binding for an action"""
        if action in self.bindings and key in self.bindings[action]:
            self.bindings[action].remove(key)
            self.current_layout = "CUSTOM"
            self.save_bindings()

    def get_key_name(self, key):
        """Get human-readable name for a key"""
        return pygame.key.name(key).upper()

    def get_bindings_for_action(self, action):
        """Get list of keys bound to an action"""
        return self.bindings.get(action, [])

    def get_bindings_display(self):
        """Get formatted string of all bindings for display"""
        display = []
        action_names = {
            "move_up": "Move Up",
            "move_down": "Move Down",
            "move_left": "Move Left",
            "move_right": "Move Right",
            "dash": "Dash",
            "light_attack": "Light Attack",
            "heavy_attack": "Heavy Attack",
            "musou_attack": "Musou Attack",
        }

        for action, name in action_names.items():
            keys = self.get_bindings_for_action(action)
            key_names = [self.get_key_name(k) for k in keys]
            display.append(f"{name}: {' / '.join(key_names)}")

        return display

    def _convert_keys_to_json(self, bindings):
        """Convert pygame key constants to JSON-serializable format"""
        json_bindings = {}
        for action, keys in bindings.items():
            json_bindings[action] = [pygame.key.name(k) for k in keys]
        return json_bindings

    def _convert_keys_from_json(self, json_bindings):
        """Convert JSON key names to pygame key constants"""
        bindings = {}
        for action, key_names in json_bindings.items():
            bindings[action] = [pygame.key.key_code(name) for name in key_names]
        return bindings


def detect_keyboard_layout():
    """Auto-detect keyboard layout based on system locale"""
    try:
        # Get system locale (use getlocale as getdefaultlocale is deprecated)
        try:
            system_locale = locale.getlocale()[0]
        except:
            system_locale = locale.getdefaultlocale()[0]

        if system_locale:
            # French locales use AZERTY
            if system_locale.startswith('fr') or system_locale.startswith('French'):
                return "AZERTY"
            # German/Austrian/Swiss locales use QWERTZ
            elif system_locale.startswith(('de', 'German')):
                return "QWERTZ"
            # Default to QWERTY for English and others
            else:
                return "QWERTY"
    except:
        pass
    return "QWERTY"


class InputManager:
    """Centralized input management with layout support"""

    def __init__(self, layout=None):
        # Auto-detect layout if not specified
        if layout is None:
            layout = detect_keyboard_layout()
        self.keybindings = KeyBindings(layout)
        self.mouse_bindings = {
            "light_attack": 0,  # Left mouse button
            "heavy_attack": 2,  # Right mouse button
        }

        # Input state
        self.keys_pressed = None
        self.mouse_pressed = None
        self.mouse_pos = (0, 0)

    def update(self):
        """Update input state (call each frame)"""
        self.keys_pressed = pygame.key.get_pressed()
        self.mouse_pressed = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()

    def is_action_pressed(self, action):
        """Check if an action is pressed (keyboard or mouse)"""
        if self.keys_pressed is None:
            self.update()

        # Check keyboard
        if self.keybindings.is_key_pressed(action, self.keys_pressed):
            return True

        # Check mouse
        if action in self.mouse_bindings:
            button = self.mouse_bindings[action]
            if self.mouse_pressed[button]:
                return True

        return False

    def get_movement_vector(self):
        """Get normalized movement vector from input"""
        move_x = 0
        move_y = 0

        if self.is_action_pressed("move_up"):
            move_y -= 1
        if self.is_action_pressed("move_down"):
            move_y += 1
        if self.is_action_pressed("move_left"):
            move_x -= 1
        if self.is_action_pressed("move_right"):
            move_x += 1

        return pygame.math.Vector2(move_x, move_y)

    def set_layout(self, layout_name):
        """Change keyboard layout"""
        return self.keybindings.set_layout(layout_name)

    def get_current_layout(self):
        """Get current layout name"""
        return self.keybindings.current_layout

    def get_available_layouts(self):
        """Get list of available layouts"""
        return self.keybindings.get_available_layouts()

    def get_bindings_display(self):
        """Get formatted bindings for UI display"""
        return self.keybindings.get_bindings_display()
