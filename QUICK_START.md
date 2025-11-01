# Quick Start Guide - 2D Musou Game

## First Time Setup

1. **Install Dependencies**
   ```bash
   cd C:\Users\Napoléon\PyCharmMiscProject\2d_musou_game
   pip install -r requirements.txt
   ```

2. **Run the Game**
   ```bash
   python main.py
   ```

## First Launch - Choose Your Layout

When you first start the game:

1. Press **F2** to open the keyboard layout menu
2. Select your keyboard type:
   - **QWERTY**: English/US keyboards
   - **AZERTY**: French/Belgian keyboards
   - **QWERTZ**: German/Austrian keyboards
   - **ARROWS**: Prefer arrow keys only
   - **IJKL**: Left-handed friendly
3. Press **Enter** to confirm
4. Press **F1** to view your controls

## Basic Gameplay

### For QWERTY Users
```
Movement:    W/A/S/D or Arrow Keys
Dash:        Shift
Light Attack: Space or Left Click
Heavy Attack: Ctrl or Right Click
Ultimate:     M
```

### For AZERTY Users
```
Movement:    Z/Q/S/D or Arrow Keys
Dash:        Shift
Light Attack: Space or Left Click
Heavy Attack: Ctrl or Right Click
Ultimate:     M
```

### For Arrow Key Users
```
Movement:    Arrow Keys Only
Dash:        Shift
Light Attack: Space or Z
Heavy Attack: X
Ultimate:     C
```

## Game Objectives

1. **Survive Enemy Waves**
   - Enemies spawn from bases around the map
   - Grunts (red) are weak but numerous
   - Officers (purple) are tougher and smarter

2. **Capture Bases**
   - Stand in the colored circles to capture them
   - Captured bases reduce enemy spawning
   - Control more bases to win!

3. **Level Up**
   - Defeat enemies to gain experience
   - Level up increases your stats
   - Survive as long as possible!

## Tips for Beginners

1. **Use Dash Wisely**
   - Dash gives invincibility frames
   - Use it to escape danger
   - Has a cooldown, don't spam it!

2. **Manage Your Musou**
   - Press M when the yellow bar is full
   - Deals massive area damage
   - Great for clearing large groups

3. **Capture Bases Strategically**
   - Reduces enemy spawn rate
   - Gives you breathing room
   - But you're vulnerable while capturing!

4. **Watch Your Health**
   - Red bar at top left
   - Enemies deal contact damage
   - Don't get surrounded!

## Keyboard Layout Issues?

### Keys Not Working?
1. Press **F1** to see current controls
2. Press **F2** to change layout
3. Try different layouts until you find one that works

### Custom Keys?
Edit `config/keybinds.json` after first launch

### Still Having Issues?
- Check if pygame is installed: `pip install pygame`
- Verify Python version: `python --version` (need 3.8+)
- See [KEYBOARD_LAYOUTS.md](KEYBOARD_LAYOUTS.md) for detailed help

## Performance Settings

### Low FPS?
- Press **F3** to see FPS counter
- Close other applications
- Reduce enemy spawn rate in code

### Debug Tools
- **F3**: Show FPS and entity count
- **F4**: Show enemy navigation paths
- **Ctrl+Q**: Quick quit

## Common Shortcuts

| Key | Action |
|-----|--------|
| F1 | Toggle controls overlay |
| F2 | Change keyboard layout |
| F3 | Debug info |
| F4 | Flow-field visualization |
| ESC | Pause menu |
| Ctrl+Q | Quit game |

## Next Steps

Once you're comfortable:
- Try different keyboard layouts (F2)
- Experiment with Musou attacks (M)
- Practice dash timing (Shift)
- Learn base capture strategy
- Check out [README_NEW.md](README_NEW.md) for advanced features

## Quick Reference Cards

### QWERTY Layout
```
┌─────────────────────────────┐
│ Movement: W/A/S/D + Arrows  │
│ Dash:     Shift             │
│ Light:    Space / LMB       │
│ Heavy:    Ctrl / RMB        │
│ Musou:    M                 │
│ Menu:     ESC               │
│ Layout:   F2                │
└─────────────────────────────┘
```

### AZERTY Layout
```
┌─────────────────────────────┐
│ Movement: Z/Q/S/D + Arrows  │
│ Dash:     Shift             │
│ Light:    Space / LMB       │
│ Heavy:    Ctrl / RMB        │
│ Musou:    M                 │
│ Menu:     ESC               │
│ Layout:   F2                │
└─────────────────────────────┘
```

### Arrow Keys Layout
```
┌─────────────────────────────┐
│ Movement: Arrow Keys        │
│ Dash:     Shift             │
│ Light:    Space / Z / LMB   │
│ Heavy:    X / RMB           │
│ Musou:    C                 │
│ Menu:     ESC               │
│ Layout:   F2                │
└─────────────────────────────┘
```

## Troubleshooting

### "Module not found" error?
```bash
pip install -r requirements.txt
```

### Game won't start?
```bash
python -c "import pygame; print('pygame OK')"
python -c "import numpy; print('numpy OK')"
```

### Controls not responding?
1. Press F2 to open layout menu
2. Try each layout
3. Check F1 for current bindings

## Have Fun!

Enjoy slaying hordes of enemies! 🎮

For more details, see:
- [README_NEW.md](README_NEW.md) - Full documentation
- [KEYBOARD_LAYOUTS.md](KEYBOARD_LAYOUTS.md) - Layout details
- [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) - Technical info
