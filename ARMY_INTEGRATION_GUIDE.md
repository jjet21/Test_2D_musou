# Army System Integration Guide

## ✅ Completed Implementation

### Files Created (All Compiled Successfully):
1. **`game/blackboard.py`** - Shared battlefield intelligence system
2. **`game/formation.py`** - Formation management with looseness & command radius
3. **`game/army_units.py`** - Unit hierarchy (soldiers/officers/generals)
4. **`game/army_ai.py`** - Strategic (General) & Tactical (Officer) AI
5. **`game/army_soldier_ai.py`** - Soldier AI with formation following
6. **`game/army_deployment.py`** - Army deployment & reinforcement system
7. **`game/army_systems.py`** - Central coordinator (ArmyManager)
8. **`ARMY_SYSTEM_DESIGN.md`** - Full design documentation

## Features Implemented

### ✅ Complete Features:
- **3-Tier Unit Hierarchy** (Soldier → Officer → General)
- **Command Influence Radius** (dynamic squad assignment)
- **4 Formation Types** (Line, Column, Wedge, Skirmish)
- **Formation Looseness** (0-1 parameter for rigid vs loose)
- **Cohesion System** (auto-regroup when formation breaks)
- **Blackboard AI** (shared battlefield intelligence)
- **Strategic AI** (General-level macro decisions)
- **Tactical AI** (Officer-level micro management)
- **Soldier AI** (formation following + combat)
- **Morale System** (affects damage and behavior)
- **Reserve Pool** (30% held back, commits when needed)
- **Threat Evaluation** (officers assess local danger)
- **Reinforcement Waves** (every 2 minutes)
- **Weighted Objectives** (center base 1.5x value)
- **Command Delays** (0.5s general→officer, 0.2s officer→soldier)

## Integration Steps

### Option 1: Replace Existing System (Recommended)

Edit `main.py`:

```python
# Add import
from game.army_systems import ArmyManager

class MusouGame:
    def __init__(self):
        # ... existing code ...

        # REPLACE old spawner/enemy AI with army system
        # Comment out or remove:
        # self.spawner = Spawner(...)
        # self.enemy_ai_system = EnemyAISystem(...)

        # ADD Army Manager
        self.army_manager = ArmyManager(
            self.engine.entity_manager,
            self.objective_system
        )

        # Initialize armies (call after engine setup)
        self.army_manager.initialize_armies(self.WORLD_WIDTH, self.WORLD_HEIGHT)

    def run(self):
        # In game loop, REPLACE spawner and enemy AI updates with:
        self.army_manager.update(dt)

        # Optional: Draw army debug info
        if self.engine.show_debug:
            self.army_manager.draw_debug(
                self.engine.screen,
                self.render_system.camera_x,
                self.render_system.camera_y
            )
```

### Option 2: Side-by-Side (Testing)

Keep both systems active temporarily:

```python
# Keep old spawner for now
self.spawner = Spawner(...)

# Add army system
self.army_manager = ArmyManager(...)
self.army_manager.initialize_armies(...)

# Update both
self.spawner.update(dt)
self.army_manager.update(dt)
```

### Option 3: Player-Controlled Army (Future)

When player becomes officer/general:

```python
# In player upgrade logic:
player = self.player
unit = player.get_component("Unit")

# Promote to officer
if player_earned_promotion:
    unit.promote_to("officer")

    # Create squad for player
    squad_id = "player_squad"
    self.army_manager.blackboard.register_squad(squad_id, player.id)
    unit.squad_id = squad_id

    # Player can now command soldiers!
```

## Testing the System

### Quick Test:
1. Run the game
2. Press F3 to enable debug view
3. You should see:
   - Blue army on left (team 0)
   - Red army on right (team 1)
   - Subtle command auras around officers/generals
   - Yellow dots showing formation positions
   - Armies marching toward center base

### Expected Behavior:
- **Start**: Both armies advance toward center base
- **Contact**: Squads engage in formation
- **Casualties**: Broken squads regroup
- **Reserves**: Generals commit reserves when losing
- **Reinforcements**: New soldiers spawn every 2 minutes
- **Morale**: Teams with more bases/units gain morale advantage

## Configuration Options

### Adjust in `army_deployment.py`:
```python
self.reinforcement_interval = 120.0  # Change wave timing
self.reinforcements_per_wave = 5     # Change wave size
```

### Adjust in `army_systems.py` (ArmyManager):
```python
self.general_ai_team0.set_objective_priority("Center Base", 2.0)  # Higher priority
```

### Adjust in `formation.py`:
```python
Formation(FormationType.LINE, looseness=0.5)  # Looser formations
```

## Visual Enhancements (Optional)

### Add to UISystem in `game/systems.py`:
```python
def draw_army_stats(self, screen, army_manager):
    """Draw morale bars and unit counts"""
    stats = army_manager.get_stats_for_ui()

    # Team 0 (player)
    morale_text = f"Morale: {int(stats['morale_team0']*100)}%"
    units_text = f"Units: {stats['team0']['total_units']}"
    # ... render text
```

## Troubleshooting

### If armies don't appear:
1. Check console for "[DEPLOYMENT]" messages
2. Verify `initialize_armies()` was called
3. Check entity manager has entities with "unit" tag

### If units don't move:
1. Enable F3 debug to see command auras
2. Check console for "[GENERAL]" / "[OFFICER]" AI messages
3. Verify blackboard has strategic goals set

### If formations are messy:
1. Increase looseness parameter (0.5-0.8 for loose)
2. Check cohesion values in blackboard
3. Ensure regrouping is triggering

### Performance issues:
1. Reduce reinforcement wave size
2. Reduce number of squads (fewer officers)
3. Increase decision_cooldown timers in AI

## Next Steps

### Immediate:
1. Integrate into main.py (Option 1 or 2)
2. Test deployment and basic movement
3. Adjust formation looseness to your preference

### Short-term:
1. Add banners/flags to officers (visual polish)
2. Add mini-map rendering
3. Tune morale/reinforcement rates

### Long-term:
1. Player promotion system (soldier → officer → general)
2. Multiple army types (cavalry, archers, etc.)
3. Terrain effects on formations
4. Fog of war / scouting mechanics

## Summary

You now have a complete army battle system with:
- ✅ 3-tier command hierarchy
- ✅ Dynamic squad assignment
- ✅ Formation warfare
- ✅ Strategic & tactical AI
- ✅ Morale & cohesion
- ✅ Reserves & reinforcements
- ✅ Weighted objectives

The system is modular, extensible, and supports player progression from soldier to general!
