# 2D Musou Game - Enhanced ECS Edition

A high-performance 2D Musou-style game built in **Python 3.13** with PyGame, featuring Entity-Component System architecture, flow-field navigation, and object pooling for handling 100-200 enemies simultaneously.

## Features

### Core Gameplay
- **Mass Combat**: Fight hundreds of weak enemies at once with smooth 60 FPS performance
- **Large Battlefields**: 3200x2400 world with capturable bases and dynamic objectives
- **Player Combat**: Light attacks, heavy attacks, and devastating Musou area attacks
- **Dash Mechanic**: Invincibility frames and high-speed movement
- **Enemy Types**:
  - **Grunts**: Basic enemies with simple AI
  - **Officers**: Tougher, faster enemies with enhanced stats

### Advanced Systems
- **Entity-Component System (ECS)**: Clean, modular architecture
- **Flow-Field Navigation**: Efficient pathfinding for large enemy groups
- **Object Pooling**: Reduces GC pressure, prevents memory churn
- **Spatial Hashing**: Optimized collision detection for hundreds of entities
- **Finite State Machine AI**: Enemies with idle, chase, and attack states
- **Capturable Bases**: Strategic objectives that affect enemy spawning
- **JSON-Driven Configuration**: Easy-to-modify enemy and objective configs
- **Multi-Layout Input System**: Support for QWERTY, AZERTY, QWERTZ, and custom layouts

### Performance Optimizations
- Object pooling for enemies and projectiles
- Spatial hashing for broad-phase collision detection
- Flow-field navigation updated every 0.5s (not per-frame)
- Dirty-rect rendering and sprite batching
- Target: 60 FPS with 100-200 enemies

## Controls

### Movement
- **WASD / Arrow Keys**: Move player (QWERTY layout)
- **ZQSD / Arrow Keys**: Move player (AZERTY layout)
- **Shift**: Dash (with invincibility frames)

### Combat
- **Space / Left Mouse**: Light attack
- **Ctrl / Right Mouse**: Heavy attack
- **M Key**: Musou attack (ultimate ability)

### Menu & Configuration
- **F1**: Toggle controls overlay
- **F2**: Change keyboard layout (QWERTY, AZERTY, QWERTZ, ARROWS, IJKL)
- **ESC**: Pause/unpause game

### Debug
- **F3**: Toggle FPS/entity counter
- **F4**: Toggle flow-field visualization
- **Ctrl+Q**: Quit game

> **Note**: The game supports multiple keyboard layouts! See [KEYBOARD_LAYOUTS.md](KEYBOARD_LAYOUTS.md) for details.

## Installation

1. Ensure Python 3.13+ is installed
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

## Project Structure

```
2d_musou_game/
├── main.py                  # Main game entry point
├── requirements.txt          # Dependencies
├── config/
│   ├── enemies.json         # Enemy spawn configuration
│   └── objectives.json      # Base/objective configuration
├── core/
│   ├── engine.py            # Game engine and systems loop
│   ├── entity.py            # Entity and EntityManager
│   ├── component.py         # Component base classes
│   ├── pool.py              # Object pooling system
│   └── spatial.py           # Spatial hashing for collisions
└── game/
    ├── player.py            # Player entity and control systems
    ├── enemy.py             # Enemy entities with FSM AI
    ├── flowfield.py         # Flow-field navigation
    ├── spawner.py           # JSON-driven enemy spawning
    ├── objective.py         # Capturable bases system
    └── systems.py           # Rendering, combat, camera, UI systems
```

## Architecture

### Entity-Component System
Entities are containers for components. Components hold data and logic:
- `Transform`: Position, velocity, rotation
- `Sprite`: Visual representation
- `Health`: HP and damage handling
- `Combat`: Attack damage, range, cooldowns
- `AI`: State machine for enemies
- `PlayerController`: Input handling and abilities

### Systems Loop
```python
while running:
    player_input_system.update(dt)
    player_attack_system.update(dt)
    enemy_ai_system.update(dt)
    collision_system.update(dt)
    combat_system.update(dt)
    camera_system.update(dt)
    render_system.draw(screen)
```

### Flow-Field Navigation
- Grid-based direction field calculated using Dijkstra's algorithm
- Each cell stores optimal direction toward player/bases
- Updated every 0.5s instead of per-frame
- Allows hundreds of enemies to pathfind efficiently

### Object Pooling
- Pre-allocates 100 grunts and 20 officers
- Reuses inactive entities instead of creating/destroying
- Reduces garbage collection pressure
- Maintains stable framerate with many entities

## Configuration

### Enemies (`config/enemies.json`)
```json
{
  "spawners": {
    "base_1": {
      "enemy": "grunt",
      "rate": 2,
      "max": 50
    }
  }
}
```

### Objectives (`config/objectives.json`)
```json
{
  "bases": [
    {
      "name": "North Base",
      "x": 1600,
      "y": 400,
      "radius": 150
    }
  ]
}
```

## Debug Features

- **F3 Debug Overlay**: Shows FPS, entity count, frame time, and pool statistics
- **F4 Flow-Field Visualization**: Displays direction vectors for enemy navigation
- **Console Commands** (planned): spawn, set_tickrate, toggle_flowfield

## Performance Targets

- **Target FPS**: 60 FPS
- **Target Enemy Count**: 100-200 simultaneous enemies
- **Tested On**: Mid-range PC (requires NumPy for flow-field math)

## Future Enhancements

- [ ] Multiple player weapons and combos
- [ ] More enemy types (ranged, tank, boss)
- [ ] Power-ups and collectibles
- [ ] Wave-based progression system
- [ ] Particle effects for attacks
- [ ] Sound effects and music
- [ ] Local co-op multiplayer
- [ ] Mini-map overlay
- [ ] Save/load system
- [ ] Achievement system

## Technical Details

### Pitfalls Prevented
- ✅ CPU spikes from pathfinding → Flow-field with periodic updates
- ✅ Frame drops from collisions → Spatial hashing + broad-phase culling
- ✅ GC/memory churn → Object pooling and sprite reuse
- ✅ Input lag → Input processed first in systems loop
- ✅ Rendering overhead → Minimal per-frame allocations

## Credits

Built with Python 3.13, PyGame, and NumPy following best practices for performance-oriented game development.

## License

Free to use and modify for learning purposes.
