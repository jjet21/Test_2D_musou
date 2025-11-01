# Changelog - 2D Musou Game

## Version 1.2.2 - Priority & Targeting System (2025-10-30)

### 🎯 New Priority Systems
- **Distance-Weighted Objective Selection**
  - Generals now factor distance when choosing targets
  - Score formula: `strategic_value / (distance/1000 + 0.5)`
  - Prefers closer objectives unless distant ones are significantly more valuable
  - Calculated from army center of mass

- **Rank-Based Combat Targeting**
  - Soldiers prioritize high-value targets: General (3x) > Officer (2x) > Soldier (1x)
  - Distance still matters but rank provides significant weight
  - Detection range: 4x attack range for early threat identification

- **Protection Priority System**
  - Soldiers defend threatened commanders: General > Officer > Self
  - General protection radius: 200 pixels
  - Officer protection radius: 150 pixels (squad's own officer prioritized)
  - Console messages: `[PROTECTION] Soldier protecting X from Y!`

### 🎨 Visual Improvements
- **Bi-Directional Base Capture Progress Bar**
  - Left half: Red (team 1) fills when capturing
  - Right half: Blue (team 0) fills when capturing
  - Center white line marks neutral point
  - Fixed issue where red capture appeared empty

### 🛡️ Team Verification
- All priority checks verify team membership
- Blue soldiers only protect blue commanders
- Red soldiers only protect red commanders
- Units only target opposite-team enemies

### 📁 Modified Files
- `main.py` - Bi-directional capture progress visualization
- `game/army_ai.py` - Distance-weighted objective selection
- `game/army_soldier_ai.py` - Priority target selection system
- `PRIORITY_SYSTEM.md` - Comprehensive system documentation

### 🔧 Technical Details

**Objective scoring:**
```
score = strategic_value / ((distance / 1000) + 0.5)
```

**Combat targeting:**
```
target_score = rank_value / ((distance / 100) + 0.5)
Ranks: general=3.0, officer=2.0, soldier=1.0
```

**Protection triggers:**
- Enemy within 200px of friendly general → attack enemy
- Enemy within 150px of squad's officer → attack enemy

### 🎮 Gameplay Impact
- **Smarter army movement**: No more cross-map marches ignoring nearby bases
- **Bodyguard behavior**: Soldiers protect their commanders
- **Focus fire**: Units concentrate on high-value targets (generals/officers)
- **Tactical depth**: Rank and positioning now critical to combat

---

## Version 1.2.1 - Movement & Capture Bugfixes (2025-10-30)

### 🐛 Critical Bug Fixes
- **Fixed officers stuck at captured objectives**
  - Officers now check if current objective is already owned
  - Automatically look for new targets after successful capture
  - Added console messages: "[OFFICER] Objective already captured!"
- **Fixed generals not moving**
  - Generals now drift continuously toward strategic objectives (speed: 30)
  - Position 70% toward officers, 30% toward objective
  - Only move when >200 pixels from ideal position
- **Fixed units spreading too far from bases**
  - CAPTURE_SPREAD formation radius: 355px → 70px (fixed)
  - Units now fit comfortably within 100px base capture radius
- **Fixed officers not reaching base centers**
  - Officers now stop at 30 pixels (was 100px) when near bases
  - Always target base center when capturing at low threat
  - Target base center at medium/high threat if >30px away

### 🎯 Tactical Improvements
- **Better target validation**: Officers won't adopt already-owned objectives
- **Smarter capture positioning**: Officers consistently move to base centers
- **More aggressive advancement**: Armies push forward continuously

### 📁 Modified Files
- `game/army_ai.py` - Officer and general movement logic
- `game/formation.py` - CAPTURE_SPREAD formation radius
- `MOVEMENT_BUGFIXES.md` - Comprehensive bug fix documentation

### 🔧 Technical Details
Officer movement changes:
- Added ownership check in `move_toward_objective()` (lines 605-617)
- Added target validation in fallback logic (lines 619-630)
- Reduced stop distance: 30px at bases, 100px elsewhere (line 779)

General movement changes:
- New `drift_toward_objective()` method (lines 347-409)
- Called every frame when not actively repositioning (line 74)
- Drift speed: 30 (vs reposition speed: 50)

### 🎮 Debug Features
- **F3 key** shows command radii and formations (already implemented)
- Visualizes officer influence (400px) and general influence (1000px)
- Shows formation positions and army statistics

---

## Version 1.2.0 - Scout System & Tactical Improvements (2025-10-30)

### ✨ New Features
- **Scout System**: Officers can deploy scouts for reconnaissance
  - Max 10% of squad can be scouts
  - Minimum 1 scout only if squad has 5+ soldiers
  - Scouts patrol 250 pixels around officer position
  - Scouts detect enemies within 300 pixels and report via console
  - Scouts avoid combat and retreat when threatened
  - Automatic deployment during low/medium threat situations
  - Scouts recalled during high threat or active combat

### 🎯 Tactical Enhancements
- **Exponential Capture Priority**: Units stay on nearly-complete captures
  - 0% progress: 1.0x priority
  - 50% progress: 1.75x priority
  - 90% progress: 3.43x priority
  - Makes it harder for enemies to interrupt near-complete captures
- **General Repositioning**: Generals dynamically reposition based on:
  - Base losses triggering strategic moves
  - Army center of mass shifting >400 pixels
  - General being >600 pixels from army
- **Extended Command Radius**:
  - Officer influence: 300→400 pixels
  - General influence: 800→1000 pixels

### 🐛 Bug Fixes
- Fixed enemy base capture (ownership mapping: -1=neutral, 0=team0, 1=team1)
- Implemented rank-based capture rates (soldier: 0.1, officer: 0.3, general: 0.5)

### 🎮 Camera Improvements
- **Zoom Controls**: 2 zoom levels
  - Normal: 1.0x (default)
  - Zoomed out: 0.5x (4x more visible area)
  - Controls: Mouse wheel or +/- keys
  - Smooth zoom transitions

### 📁 Modified Files
- `game/blackboard.py` - Added scout tracking and reporting system
- `game/army_ai.py` - Added scout management to OfficerAI
- `game/army_soldier_ai.py` - Added scout patrol behavior
- `game/systems.py` - Added zoom controls to CameraSystem
- `game/objective.py` - Fixed ownership mapping and rank-based capture
- `game/formation.py` - Extended command influence radii
- `TACTICAL_IMPROVEMENTS.md` - Updated implementation status
- `CHANGELOG.md` - This file

### 🔧 Technical Details
Scout behavior:
- Deployed every 5 seconds if conditions met
- Patrol in circular pattern around officer
- Report enemy rank and position to console
- Move at 100 speed (patrol), 140 speed (retreat)
- Detection range: 300 pixels

---

## Version 1.1.2 - Visual Improvements (2025-10-27)

### ✨ New Features
- **Visible Attack Animations**: Attacks now show as colored expanding circles
  - Light attack: Yellow (60 range)
  - Heavy attack: Orange (90 range)
  - Musou attack: Purple (180 range)
- **Improved Enemy Sprites**:
  - Grunts increased from 24x24 to 32x32 pixels
  - Officers increased from 32x32 to 40x40 pixels
  - Added black outlines for better visibility
  - Enhanced eyes with pupils
  - Officers have golden crowns

### 🎨 Visual Enhancements
- Attack effects fade out smoothly over duration
- Glowing center with transparent outer ring
- Color-coded attacks by type
- Better enemy distinction

### 🐛 Bug Fixes
- Added error handling in ObjectiveSystem to prevent crashes near bases

### 📁 New Files
- `game/attack.py` - Attack visualization system

### 📁 Modified Files
- `main.py` - Integrated AttackSystem
- `game/enemy.py` - Improved enemy sprites
- `game/objective.py` - Added error handling

---

## Version 1.1.1 - Bugfix Release (2025-10-27)

### 🐛 Bug Fixes
- Fixed rendering crash when sprite surfaces were None
- Fixed enemies not being visible after spawning from object pool
- Fixed keyboard layout not auto-detecting for French/German users

### 🌍 Keyboard Auto-Detection
- Now automatically detects AZERTY for French locales (fr_FR, fr_BE)
- Now automatically detects QWERTZ for German locales (de_DE, de_AT, de_CH)
- Falls back to QWERTY for other locales
- Users can still manually change layout with F2

### 🔧 Technical Changes
- Added null check in RenderSystem for sprite surfaces
- Reset sprite visibility when acquiring entities from pool
- Improved locale detection with fallback handling
- Fixed Python 3.15 deprecation warning for locale.getdefaultlocale()

### 📁 Files Modified
- `game/systems.py` - Added sprite surface null check
- `game/spawner.py` - Reset sprite visibility on pool reuse
- `core/input_config.py` - Added keyboard auto-detection
- `main.py` - Use auto-detection for InputManager

---

## Version 1.1.0 - Keyboard Compatibility Update (2025-10-27)

### 🌍 International Keyboard Support
- Added support for 5 keyboard layouts: QWERTY, AZERTY, QWERTZ, ARROWS, IJKL
- Instant layout switching with F2 key
- Persistent configuration saved to JSON
- No restart required

### 🎮 New UI Features
- **F1**: Controls overlay showing current keybindings
- **F2**: Keyboard layout selection menu
- **ESC**: Enhanced pause menu with controls option
- Visual preview of keybindings for each layout

### 🔧 Technical Improvements
- New `InputManager` class for centralized input handling
- Action-based input system (layout-agnostic)
- `KeyBindings` class with JSON serialization
- Backward compatible with direct key checking

### 📁 New Files
- `core/input_config.py` - Input management system
- `game/menu.py` - Menu system with keyboard configuration
- `config/keybinds.json` - User keyboard preferences (auto-generated)
- `KEYBOARD_LAYOUTS.md` - Layout documentation
- `QUICK_START.md` - Quick start guide
- `KEYBOARD_COMPATIBILITY_SUMMARY.md` - Feature summary

### 🔄 Modified Files
- `main_new.py` - Integrated InputManager and menus
- `game/player.py` - Updated input systems
- `README_NEW.md` - Added keyboard documentation

### 🎯 Supported Layouts

#### QWERTY (English/US)
- Movement: W/A/S/D or Arrow Keys
- Standard English keyboard layout

#### AZERTY (French/Belgian)
- Movement: Z/Q/S/D or Arrow Keys
- Native French keyboard support

#### QWERTZ (German/Austrian/Swiss)
- Movement: W/A/S/D or Arrow Keys
- Native German keyboard support

#### ARROWS (Universal)
- Movement: Arrow Keys only
- Attacks: Space/Z/X/C
- Ideal for traditional controls

#### IJKL (Left-handed)
- Movement: I/J/K/L or Arrow Keys
- Attacks: U/O
- Left-handed friendly layout

### 🐛 Bug Fixes
- None (new feature)

### 📝 Notes
- Default layout is QWERTY
- Layout preference persists between sessions
- Custom layouts can be created by editing `config/keybinds.json`
- All layouts support mouse controls as alternative

---

## Version 1.0.0 - Initial Release (2025-10-27)

### Core Features
- Entity-Component System architecture
- Flow-field navigation for 100-200 enemies
- Object pooling for performance
- Spatial hashing for collision detection
- FSM-based enemy AI
- Capturable bases system
- JSON-driven configuration

### Gameplay
- Player with dash, light attack, heavy attack, and Musou ultimate
- Two enemy types: Grunts and Officers
- 5 capturable bases
- Wave-based spawning
- Experience and leveling system

### Technical
- 60 FPS target with 100-200 enemies
- NumPy-based flow-field calculations
- Pre-allocated entity pools
- Optimized collision detection
- Debug overlay (F3)
- Flow-field visualization (F4)

### Documentation
- README_NEW.md - Complete documentation
- DEVELOPMENT_SUMMARY.md - Technical details
- basis.txt - Original specification
- Config files for enemies and objectives

---

## Roadmap

### Version 1.2.0 (Planned)
- [ ] Gamepad/controller support
- [ ] In-game key remapping interface
- [ ] More enemy types (ranged, tank, boss)
- [ ] Particle effects for attacks
- [ ] Sound effects and music

### Version 1.3.0 (Planned)
- [ ] Power-ups and collectibles
- [ ] Wave progression system
- [ ] Achievement system
- [ ] Local co-op multiplayer

### Version 2.0.0 (Future)
- [ ] Save/load system
- [ ] Main menu and settings
- [ ] Multiple maps/arenas
- [ ] Weapon variety
- [ ] Advanced upgrade system
