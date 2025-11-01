# Army Battle System - Design Document

## Overview
Transforming the game from individual combat into large-scale army battles with strategic command hierarchy.

## Core Features

### 1. Unit Hierarchy
```
General (1 per team)
  └─> Officers (3-5 per team)
       └─> Soldiers (5-10 per squad)
```

**Unit Stats:**
- **Soldier**: 50 HP, 10 damage, 32x32 sprite
- **Officer**: 150 HP, 20 damage, 48x48 sprite, commands up to 10 soldiers
- **General**: 300 HP, 40 damage, 64x64 sprite, commands all officers

**Player Progression:**
- Player starts as soldier (no command)
- Can promote to Officer (future feature)
- Can promote to General (future feature)

### 2. Command Influence System
**Dynamic radius-based command:**
- Generals: 800px influence radius
- Officers: 300px influence radius
- Soldiers follow nearest officer in range
- Officers follow their general
- Visual auras show command radius (subtle glow)

**Benefits:**
- No manual reassignment needed
- Armies automatically reorganize when commanders die
- Natural squad formation emergence

### 3. Formation System
**Formation Types:**
- **LINE**: Defensive, wide front (looseness: 0.2)
- **COLUMN**: Marching, 2-wide (looseness: 0.4)
- **WEDGE**: Assault, V-shape (looseness: 0.3)
- **SKIRMISH**: Loose, irregular (looseness: 0.8)

**Looseness Parameter (0-1):**
- 0 = Rigid parade formation
- 1 = Loose skirmish formation
- Affects spacing variance and pathfinding flexibility

**Formation Intelligence:**
- Officers choose formation based on orders:
  - DEFEND → LINE formation
  - MOVE → COLUMN formation
  - ATTACK → WEDGE formation
  - SKIRMISH → SKIRMISH formation

**Cohesion & Regrouping:**
- System calculates how well units match formation
- If cohesion < 0.3 → Formation breaks
- Officer issues REGROUP order (3 second duration)
- Switches to COLUMN for easier reformation
- Resume normal orders after regroup complete

### 4. Blackboard System
**Shared Battlefield Intelligence:**

**Strategic Layer (General writes):**
- Current objective ("attack_base", "defend_base", "advance", "retreat")
- Target position/base
- Strategic priority

**Tactical Layer (Officer writes):**
- Squad assignments (officer_id → soldier_ids)
- Squad positions and targets
- Formation type and cohesion

**Intelligence Layer (All units write):**
- Known enemy positions
- Threat levels by location
- Base ownership status
- Team morale (0-1)
- Squad cohesion (0-1)

**Command Delays (Realistic coordination):**
- General → Officer: 0.5 second delay
- Officer → Soldier: 0.2 second delay
- Prevents robotic instant coordination

### 5. Morale & Cohesion Mechanics

**Team Morale (0-1):**
- Affects combat effectiveness (0.5x to 1.0x damage multiplier)
- Decreases with: casualties, lost bases, retreats
- Increases with: captured bases, victories, successful charges

**Squad Cohesion (0-1):**
- How well squad maintains formation
- Decreases with: scattered positions, casualties, panic
- Below 0.3 → Formation breaks, must regroup

**Officer Morale Threshold:**
- If squad morale < 0.3 → Automatic retreat
- If squad strength < 40% → Request reinforcements

### 6. Strategic AI (General)

**Decision Loop (every 2 seconds):**

```
IF we have no bases AND enemy has bases:
    → DESPERATE_ATTACK (commit all reserves, attack nearest)

ELSE IF enemy bases > our bases:
    → ATTACK (target weighted high-value enemy bases)

ELSE IF neutral bases exist:
    → EXPAND (capture weighted neutral bases)

ELSE IF our units < enemy units × 0.7:
    → DEFEND (protect highest-value base we own)

ELSE:
    → ADVANCE (pressure enemy positions)
```

**Weighted Objectives:**
- Each base has strategic value multiplier (default: 1.0)
- Center base: 1.5x importance
- Corner bases: 1.0x importance
- General prioritizes high-value targets

**Reserve Management:**
- Keep 30% of squads in reserve (default)
- Commit reserves when:
  - Numerical inferiority (units < enemy × 0.8)
  - Base lost
  - Team morale < 0.4

### 7. Tactical AI (Officer)

**Threat Evaluation (every 1 second):**

```python
local_superiority = friendly_units / (friendly_units + enemy_units)
threat_ratio = calculate_from_superiority(local_superiority)

IF threat_ratio > 1.5:
    → RETREAT (fall back to safer position)

ELSE IF squad_morale < 0.3:
    → RETREAT (squad broken)

ELSE IF squad_strength < 40%:
    → REQUEST_REINFORCEMENTS (ask general for help)

ELSE IF formation_cohesion < 0.3:
    → REGROUP (reform formation before continuing)

ELSE:
    → EXECUTE_ORDER (follow general's strategic goal)
```

**Local Decision Making:**
- Officers evaluate 400px radius around position
- Make tactical decisions independent of general
- Can override orders to retreat if threatened
- Request reinforcements when squad depleted

### 8. Soldier AI

**Simple Behavior:**
1. Find nearest officer in 300px radius
2. Get assigned formation position from officer
3. Move toward formation position
4. Engage enemies in attack range
5. Apply morale modifier to damage

**Formation Following:**
- Each soldier assigned ideal (x, y) in formation
- Use pathfinding to reach position
- Stay close to squadmates
- Break formation to engage nearby enemies

### 9. Map Layout & Deployment

**World Size:** 3200 × 2400 pixels

**Base Placement (encourages flanking):**
```
Top Left (400, 600)     [Player]
Top Right (2800, 600)   [Enemy]
Bottom Left (400, 1800) [Player]
Bottom Right (2800, 1800) [Enemy]
Center (1600, 1200)     [Neutral - 1.5x value]
```

**Initial Deployment:**
- **Player Army (Left side, x=400):**
  - 1 General (x=400, y=1200)
  - 3 Officers (x=400, y=800/1200/1600)
  - 30 Soldiers (10 per officer squad)

- **Enemy Army (Right side, x=2800):**
  - 1 General (x=2800, y=1200)
  - 3 Officers (x=2800, y=800/1200/1600)
  - 30 Soldiers (10 per officer squad)

**Reinforcement Waves:**
- Every 2 minutes: spawn 5 soldiers per team
- Distribute to squads with lowest strength
- Maintains battle intensity

### 10. Visual Enhancements

**Unit Sprites:**
- **Soldiers**: Small team-colored circles (blue/red)
- **Officers**: Medium with gold/silver trim + chevrons
- **Generals**: Large with golden crown + star insignia

**Command Auras:**
- Subtle rings showing influence radius
- Officers: 300px pale glow
- Generals: 800px faint glow
- Only visible when F3 debug enabled

**Banners/Flags:**
- Officers carry small flags above sprite
- Generals carry large flags
- Team-colored for quick identification

**Mini-map (optional):**
- 200×150px in top-right corner
- Show bases (circles)
- Show units (colored dots)
- Show player position (highlight)

## File Structure

### New Files Created:
```
game/
├── blackboard.py        # Shared battlefield intelligence
├── formation.py         # Formation system with looseness
├── army_units.py        # Unit hierarchy (soldiers/officers/generals)
├── army_ai.py          # General & Officer AI
├── army_deployment.py  # (TO CREATE) Initial army setup
└── army_systems.py     # (TO CREATE) Update systems integration
```

### Files to Modify:
```
main.py                 # Integrate army systems
game/enemy.py          # Remove old spawner logic
game/spawner.py        # Adapt for reinforcements
```

## Implementation Status

✅ Blackboard system (shared intelligence)
✅ Formation system (types, looseness, cohesion)
✅ Command influence radius system
✅ Unit hierarchy (soldier/officer/general creation)
✅ General AI (strategic decision making)
✅ Officer AI (tactical squad management)

🚧 IN PROGRESS:
- Soldier AI updates (formation following)
- Army deployment system
- Integration with main game loop
- Visual enhancements (auras, banners)

⏳ TODO:
- Reinforcement wave system
- Mini-map rendering
- Morale visual feedback
- Sound effects for commands
