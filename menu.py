"""
Menu system with keyboard configuration
"""
import pygame


class Menu:
    """Base menu class"""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.active = False

    def handle_event(self, event):
        """Override in subclasses"""
        pass

    def update(self, dt):
        """Override in subclasses"""
        pass

    def draw(self):
        """Override in subclasses"""
        pass


class KeyboardConfigMenu(Menu):
    """Menu for configuring keyboard layout"""
    def __init__(self, screen, input_manager):
        super().__init__(screen)
        self.input_manager = input_manager
        self.selected_index = 0
        self.layouts = input_manager.get_available_layouts()
        self.current_layout = input_manager.get_current_layout()

    def handle_event(self, event):
        """Handle keyboard events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.layouts)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.layouts)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Select layout
                selected_layout = self.layouts[self.selected_index]
                if self.input_manager.set_layout(selected_layout):
                    self.current_layout = selected_layout
                    print(f"Switched to {selected_layout} layout")
            elif event.key == pygame.K_ESCAPE:
                # Close menu
                self.active = False

    def draw(self):
        """Draw the menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font.render("KEYBOARD LAYOUT", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect)

        # Current layout
        current = self.small_font.render(f"Current: {self.current_layout}", True, (100, 255, 100))
        current_rect = current.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(current, current_rect)

        # Layout options
        start_y = 220
        for i, layout in enumerate(self.layouts):
            color = (255, 255, 100) if i == self.selected_index else (255, 255, 255)
            prefix = "→ " if i == self.selected_index else "  "

            text = self.font.render(f"{prefix}{layout}", True, color)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, start_y + i * 50))
            self.screen.blit(text, text_rect)

        # Instructions
        instructions = [
            "↑/↓: Navigate",
            "Enter/Space: Select",
            "ESC: Close"
        ]

        inst_y = self.screen.get_height() - 150
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (200, 200, 200))
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, inst_y))
            self.screen.blit(text, text_rect)
            inst_y += 30

        # Show keybindings for selected layout
        bindings_y = self.screen.get_height() - 300
        bindings_title = self.small_font.render("Key Bindings:", True, (255, 255, 100))
        self.screen.blit(bindings_title, (50, bindings_y))

        # Temporarily set layout to show bindings
        temp_layout = self.layouts[self.selected_index]
        original_layout = self.input_manager.get_current_layout()
        self.input_manager.keybindings.set_layout(temp_layout)

        bindings = self.input_manager.get_bindings_display()
        for i, binding in enumerate(bindings[:8]):  # Show first 8 bindings
            text = self.small_font.render(binding, True, (200, 200, 200))
            self.screen.blit(text, (50, bindings_y + 30 + i * 25))

        # Restore original layout
        self.input_manager.keybindings.set_layout(original_layout)


class ControlsDisplayOverlay:
    """Overlay showing current controls"""
    def __init__(self, screen, input_manager):
        self.screen = screen
        self.input_manager = input_manager
        self.font = pygame.font.Font(None, 20)
        self.visible = False

    def toggle(self):
        """Toggle visibility"""
        self.visible = not self.visible

    def draw(self):
        """Draw controls overlay"""
        if not self.visible:
            return

        # Background panel
        panel_width = 300
        panel_height = 250
        panel_x = self.screen.get_width() - panel_width - 10
        panel_y = 10

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (panel_x, panel_y))

        # Title
        title = self.font.render("Controls (F1 to hide)", True, (255, 255, 100))
        self.screen.blit(title, (panel_x + 10, panel_y + 10))

        # Layout
        layout_text = f"Layout: {self.input_manager.get_current_layout()}"
        layout = self.font.render(layout_text, True, (100, 255, 100))
        self.screen.blit(layout, (panel_x + 10, panel_y + 35))

        # Bindings
        bindings = self.input_manager.get_bindings_display()
        y_offset = 60
        for binding in bindings:
            text = self.font.render(binding, True, (255, 255, 255))
            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
            y_offset += 22

        # Extra info
        extra_info = [
            "F1: Toggle controls",
            "F2: Change layout",
            "F3: Debug info",
            "F4: Flow field"
        ]
        y_offset += 10
        for info in extra_info:
            text = self.font.render(info, True, (150, 150, 150))
            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
            y_offset += 20


class PauseMenu(Menu):
    """Pause menu"""
    def __init__(self, screen):
        super().__init__(screen)
        self.options = ["Resume", "Controls", "Quit"]
        self.selected_index = 0

    def handle_event(self, event):
        """Handle keyboard events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.options[self.selected_index].lower()
            elif event.key == pygame.K_ESCAPE:
                return "resume"
        return None

    def draw(self):
        """Draw pause menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font.render("PAUSED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(title, title_rect)

        # Options
        start_y = 300
        for i, option in enumerate(self.options):
            color = (255, 255, 100) if i == self.selected_index else (255, 255, 255)
            prefix = "→ " if i == self.selected_index else "  "

            text = self.font.render(f"{prefix}{option}", True, color)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, start_y + i * 60))
            self.screen.blit(text, text_rect)
