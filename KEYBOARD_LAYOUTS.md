# Keyboard Layout Support

The game now supports multiple keyboard layouts and custom keybindings!

## Supported Keyboard Layouts

### 1. QWERTY (Default)
Standard English keyboard layout.
- **Movement**: W/A/S/D or Arrow Keys
- **Dash**: Shift
- **Light Attack**: Space
- **Heavy Attack**: Ctrl
- **Musou**: M

### 2. AZERTY
French keyboard layout.
- **Movement**: Z/Q/S/D or Arrow Keys
- **Dash**: Shift
- **Light Attack**: Space
- **Heavy Attack**: Ctrl
- **Musou**: M

### 3. QWERTZ
German keyboard layout.
- **Movement**: W/A/S/D or Arrow Keys
- **Dash**: Shift
- **Light Attack**: Space
- **Heavy Attack**: Ctrl
- **Musou**: M

### 4. ARROWS
Arrow keys only layout.
- **Movement**: Arrow Keys
- **Dash**: Shift
- **Light Attack**: Space or Z
- **Heavy Attack**: X
- **Musou**: C

### 5. IJKL
Alternative movement keys (useful for left-handed players).
- **Movement**: I/J/K/L or Arrow Keys
- **Dash**: Shift
- **Light Attack**: Space
- **Heavy Attack**: U
- **Musou**: O

## How to Change Keyboard Layout

### In-Game Menu
1. Press **F2** during gameplay
2. Use **↑/↓** arrows to navigate layouts
3. Press **Enter** or **Space** to select a layout
4. Press **ESC** to close the menu

### From Pause Menu
1. Press **ESC** to pause
2. Navigate to "Controls"
3. Select your preferred layout

### View Current Controls
Press **F1** to toggle the controls overlay, which shows:
- Current keyboard layout
- All keybindings
- Available function keys

## Universal Controls

These work regardless of your keyboard layout:

- **F1**: Toggle controls overlay
- **F2**: Change keyboard layout
- **F3**: Toggle debug info (FPS, entity count)
- **F4**: Toggle flow-field visualization
- **ESC**: Pause/unpause game
- **Ctrl+Q**: Quit game

## Mouse Controls

Mouse controls work with all keyboard layouts:
- **Left Mouse Button**: Light attack (alternative to keyboard)
- **Right Mouse Button**: Heavy attack (alternative to keyboard)

## Configuration File

Your selected keyboard layout is automatically saved to:
```
config/keybinds.json
```

This file is loaded automatically when you start the game.

### Manual Configuration

You can manually edit `config/keybinds.json` to create custom keybindings:

```json
{
  "layout": "CUSTOM",
  "bindings": {
    "move_up": ["w", "up"],
    "move_down": ["s", "down"],
    "move_left": ["a", "left"],
    "move_right": ["d", "right"],
    "dash": ["left shift", "right shift"],
    "light_attack": ["space"],
    "heavy_attack": ["left ctrl", "right ctrl"],
    "musou_attack": ["m"]
  }
}
```

## Adding Custom Layouts

Developers can add custom layouts by editing `core/input_config.py`:

```python
"MY_LAYOUT": {
    "move_up": [pygame.K_w, pygame.K_UP],
    "move_down": [pygame.K_s, pygame.K_DOWN],
    "move_left": [pygame.K_a, pygame.K_LEFT],
    "move_right": [pygame.K_d, pygame.K_RIGHT],
    "dash": [pygame.K_LSHIFT, pygame.K_RSHIFT],
    "light_attack": [pygame.K_SPACE],
    "heavy_attack": [pygame.K_LCTRL, pygame.K_RCTRL],
    "musou_attack": [pygame.K_m],
}
```

## Compatibility

### International Keyboards
The system supports multiple keyboard layouts commonly used around the world:
- **QWERTY**: English, US
- **AZERTY**: French, Belgian
- **QWERTZ**: German, Austrian, Swiss

### Accessibility
- **Arrow Keys Layout**: For players who prefer traditional arrow key controls
- **IJKL Layout**: For left-handed players
- **Mouse Support**: All attacks can be triggered with mouse buttons

## Troubleshooting

### Layout Not Saving
- Ensure the `config/` directory exists
- Check file permissions for `config/keybinds.json`
- The game creates this file automatically on first layout change

### Keys Not Responding
- Press **F1** to check current keybindings
- Try switching to a different layout with **F2**
- Check if your keyboard layout is supported by your OS

### Custom Keys Not Working
- Verify key names in `config/keybinds.json` match pygame key names
- Use lowercase for key names (e.g., "space", "left shift")
- Test with a preset layout first to ensure the system works

## Technical Details

### Architecture
- **InputManager**: Central input handling system
- **KeyBindings**: Manages layout presets and custom bindings
- **JSON Configuration**: Persistent storage of user preferences

### Performance
- Input polling happens once per frame
- No performance impact from multiple keybinding checks
- Seamless layout switching without restart

## Future Enhancements

Planned features:
- [ ] In-game key remapping interface
- [ ] Gamepad/controller support
- [ ] Profile system (multiple players)
- [ ] Key conflict detection
- [ ] Visual key prompt overlay

## Feedback

If you need support for a specific keyboard layout, please create an issue with:
- Layout name and country
- Movement key arrangement
- Any special keys or requirements
