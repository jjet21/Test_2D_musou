# Tactical Improvements & Amendments

## Document Purpose
This document outlines identified issues, proposed solutions, and refinements for the 2D Musou Game tactical systems.

---

## Issue #1: Generals Not Moving

### Problem Description
Generals remain stationary at their deployment positions and do not move toward objectives or lead their armies.

### Root Cause Analysis
- **Hypothesis 1**: Generals may not have movement logic implemented
- **Hypothesis 2**: Generals may be calculating strategic positions but not translating them to movement
- **Hypothesis 3**: General formations may be keeping them locked in place

### Proposed Solutions

#### **Option A: General as Mobile Command Post (RECOMMENDED)**
```python
# General moves slowly toward strategic objectives
# Pulls entire army with them via command influence

Behavior:
- Calculate strategic center of mass of all friendly units
- Move toward this center slowly (40-60 speed vs officer's 80)
- When objective is assigned, move 70% of the way there
- Stay behind front line by 200-300 pixels
- Officers and their squads follow general's movement
```

**Pros:**
- Realistic command behavior
- Creates natural army cohesion
- Generals safer but still mobile

**Cons:**
- More complex positioning logic

#### **Option B: Static Command Post with Dynamic Repositioning**
```python
# General stays put most of the time
# Only relocates when strategic situation changes dramatically

Triggers for movement:
- Lost all nearby bases
- Army split into distant groups
- Base captured requiring new command position
- Overwhelming threat forcing retreat
```

**Pros:**
- Simpler to implement
- Feels like historical generals (command from rear)

**Cons:**
- May feel static and unengaging

#### **Option C: Formation-Following Movement**
```python
# General moves to maintain position relative to officers

Calculate:
- Average position of all officers on team
- Move general to stay within 300-500 pixels of this center
- Maintain GENERAL_BOX formation around general as they move
```

### Recommended Implementation
**Combination of A + C:**
1. General calculates average position of all their officers
2. Moves toward this position slowly (50 speed)
3. Also considers strategic objective direction
4. Final position = weighted average (60% officer center, 40% objective)
5. Officers follow general via command influence
6. Creates natural "center of command" that advances with army

---

## Issue #2: Camera Zoom Controls

### Problem Description
No ability to zoom out and see larger battlefield overview.

### Proposed Solution

#### **Keybind Design**
```
Mouse Wheel Up / [+] Key: Zoom Out (2 levels)
Mouse Wheel Down / [-] Key: Zoom In (return to normal)

Zoom Levels:
- Level 1 (Default): 1.0x scale - Normal view
- Level 2 (Zoomed Out): 0.5x scale - 4x more area visible
```

#### **Implementation Plan**
```python
# File: core/engine.py or main.py

class CameraSystem:
    def __init__(self, ...):
        self.zoom_level = 1.0  # 1.0 = normal, 0.5 = zoomed out
        self.target_zoom = 1.0
        self.zoom_speed = 2.0  # Smooth transition

    def handle_zoom_input(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:  # Scroll up
                self.target_zoom = 0.5  # Zoom out
            else:  # Scroll down
                self.target_zoom = 1.0  # Zoom in

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.target_zoom = 0.5
            elif event.key == pygame.K_MINUS:
                self.target_zoom = 1.0

    def update(self, dt):
        # Smooth zoom transition
        if self.zoom_level != self.target_zoom:
            diff = self.target_zoom - self.zoom_level
            self.zoom_level += diff * self.zoom_speed * dt

    def render(self, screen, entities):
        # Scale all rendering by zoom_level
        # Option 1: Scale individual sprites
        # Option 2: Use pygame.transform.scale on entire surface
        # Option 3: Adjust camera offset calculations
```

#### **Rendering Strategy**
```python
# Option A: Scale entire screen (simplest)
scaled_surface = pygame.transform.scale(
    game_surface,
    (int(screen_width / zoom_level), int(screen_height / zoom_level))
)
screen.blit(scaled_surface, (0, 0))

# Option B: Adjust camera viewport (more performant)
camera.viewport_width = screen_width / zoom_level
camera.viewport_height = screen_height / zoom_level
```

#### **UI Considerations**
- HUD elements should NOT scale (always readable)
- Mini-map should adjust to show zoom level indicator
- Particle effects can scale (less visual clutter when zoomed out)

### Recommended Implementation
**Option B (Viewport adjustment)** for better performance with many units.

---

## Issue #3: Enemies Can't Capture Points

### Problem Description
Enemy units (team 1) can reduce capture progress to neutral but cannot fully capture bases.

### Root Cause Analysis
```python
# Current logic in objective.py:
if self.capture_progress < 0.3:
    self.owner = 2  # Enemy (team 1)
elif self.capture_progress > 0.7:
    self.owner = 1  # Player (team 0)
else:
    self.owner = 0  # Neutral

# The issue: team numbering mismatch
# Game uses: team 0 = player/blue, team 1 = enemy/red
# Base ownership uses: owner 1 = player, owner 2 = enemy
```

### Proposed Fix
```python
# File: game/objective.py

class Base:
    def __init__(self, ...):
        # Change ownership system to match team IDs
        self.owner = -1  # -1 = neutral, 0 = team 0, 1 = team 1
        self.capture_progress = 0.5  # 0.0 = full team 1, 1.0 = full team 0

    def update(self, dt, team0_power, team1_power):
        # Calculate capture influence
        net_influence = (team0_power - team1_power) * self.capture_rate * dt

        self.capture_progress += net_influence
        self.capture_progress = max(0.0, min(1.0, self.capture_progress))

        # Update ownership with correct team mapping
        old_owner = self.owner
        if self.capture_progress < 0.3:
            self.owner = 1  # Team 1 (enemy/red)
        elif self.capture_progress > 0.7:
            self.owner = 0  # Team 0 (player/blue)
        else:
            self.owner = -1  # Neutral

        return old_owner != self.owner

# Update all functions that check base ownership
def get_player_bases(self):
    return [b for b in self.bases if b.owner == 0]

def get_enemy_bases(self):
    return [b for b in self.bases if b.owner == 1]

def get_neutral_bases(self):
    return [b for b in self.bases if b.owner == -1]
```

### Testing Checklist
- [ ] Enemy units reduce capture_progress toward 0.0
- [ ] When progress < 0.3, base owner becomes 1 (enemy team)
- [ ] Enemy general receives captured base in strategic calculations
- [ ] Flow field updates to target enemy-owned bases
- [ ] Console messages show correct ownership

---

## Issue #4: Combat vs Capture Priority

### Problem Description
Units prioritize capturing bases even when under heavy attack or when retreat is necessary. Need dynamic priority system based on:
- Threat level
- Capture completion percentage
- Squad health/morale
- Tactical situation

### Proposed Priority System

#### **Priority Formula**
```python
capture_priority = base_priority * (1.0 - threat_modifier) * capture_progress_bonus

Where:
- base_priority = 1.0 (default capture importance)
- threat_modifier = 0.0 (low) to 1.0 (overwhelming)
- capture_progress_bonus = 1.0 + (capture_completion * 2.0)
```

#### **Priority Values**
```
Threat Level -> Modifier -> Effective Priority
Low (0.7+)      0.0         1.0 - 3.0 (based on progress)
Medium (0.5)    0.3         0.7 - 2.1
High (0.3)      0.6         0.4 - 1.2
Overwhelming    1.0         0.0 (always retreat)

Capture Progress Bonus:
0%   complete: 1.0x priority
25%  complete: 1.5x priority
50%  complete: 2.0x priority
75%  complete: 2.5x priority
90%  complete: 2.8x priority (almost done!)
```

#### **Decision Tree**
```python
def decide_squad_action(threat_level, capture_progress, squad_morale):
    # Calculate effective priorities
    capture_priority = calculate_capture_priority(capture_progress, threat_level)
    combat_priority = calculate_combat_priority(threat_level, squad_morale)
    retreat_priority = calculate_retreat_priority(threat_level, squad_morale)

    # Choose highest priority action
    if retreat_priority > combat_priority and retreat_priority > capture_priority:
        return "RETREAT"
    elif combat_priority > capture_priority:
        return "COMBAT"
    else:
        return "CAPTURE"

# Example calculations:
def calculate_capture_priority(capture_progress, threat_level):
    base = 1.0
    progress_bonus = 1.0 + (capture_progress * 2.0)  # 1.0 to 3.0
    threat_penalty = get_threat_modifier(threat_level)  # 0.0 to 1.0

    return base * progress_bonus * (1.0 - threat_penalty)

def calculate_combat_priority(threat_level, squad_morale):
    if threat_level == "low":
        return 0.3  # Can ignore and capture
    elif threat_level == "medium":
        return 0.8  # Should fight but not critical
    elif threat_level == "high":
        return 1.5  # Must fight
    else:  # overwhelming
        return 0.0  # Don't fight, retreat!

def calculate_retreat_priority(threat_level, squad_morale):
    if threat_level == "overwhelming":
        return 2.0  # Always retreat
    elif threat_level == "high" and squad_morale < 0.4:
        return 1.8  # Morale broken
    elif threat_level == "medium" and squad_morale < 0.2:
        return 1.5  # Panic retreat
    else:
        return 0.0  # Hold ground
```

#### **Behavioral Examples**

**Scenario 1: Early Capture, High Threat**
```
Capture Progress: 10%
Threat Level: High
Capture Priority: 1.0 * 1.2 * 0.4 = 0.48
Combat Priority: 1.5
Decision: COMBAT (abandon capture, fight enemies)
```

**Scenario 2: Nearly Complete, Medium Threat**
```
Capture Progress: 85%
Threat Level: Medium
Capture Priority: 1.0 * 2.7 * 0.7 = 1.89
Combat Priority: 0.8
Decision: CAPTURE (finish capture despite enemies)
```

**Scenario 3: Mid Capture, Overwhelming Threat**
```
Capture Progress: 50%
Threat Level: Overwhelming
Capture Priority: 1.0 * 2.0 * 0.0 = 0.0
Retreat Priority: 2.0
Decision: RETREAT (abandon everything)
```

### Implementation Plan
```python
# File: game/army_ai.py - OfficerAI class

def update(self, dt, entity_manager, officer_entity, game_time, objective_system):
    # ... existing code ...

    # NEW: Calculate action priorities
    action = self.decide_tactical_action(
        threat_level,
        nearest_base,
        base_distance,
        unit
    )

    if action == "RETREAT":
        self.initiate_retreat()
        self.formation_manager.change_formation_for_order(self.squad_id, "move")
    elif action == "COMBAT":
        self.engage_nearby_enemies()
        self.formation_manager.change_formation_for_order(self.squad_id, "defend")
    elif action == "CAPTURE":
        self.move_to_capture_base(nearest_base)
        if threat_level == "low":
            self.formation_manager.change_formation_for_order(self.squad_id, "capture")
```

---

## Issue #5: Soldier Movement & Scout System

### Problem Description
Multiple issues:
1. Some soldiers not moving at all
2. Soldiers too far from officer (beyond command radius)
3. No scout system implemented
4. Need defined limits on scout deployment

### Root Cause Analysis

#### **Soldiers Not Moving**
Possible causes:
- Formation positions not being updated
- Velocity not being applied
- Stuck in idle state
- No formation position assigned

#### **Soldiers Too Far from Officer**
Causes:
- Command influence radius too small (300 pixels)
- Formation positions outside radius
- Soldiers chasing enemies beyond radius
- No "rally back" behavior when too far

### Proposed Solutions

#### **A. Fix Soldier Movement**
```python
# File: game/army_soldier_ai.py

def update(self, dt, soldier_entity):
    transform = soldier_entity.get_component("Transform")
    unit = soldier_entity.get_component("Unit")

    if not transform or not unit:
        print(f"[SOLDIER DEBUG] Missing components!")
        return

    # Debug output for stationary soldiers
    if abs(transform.vx) < 0.1 and abs(transform.vy) < 0.1:
        officer = self.find_commanding_officer(soldier_entity)
        if officer:
            print(f"[SOLDIER {soldier_entity.id}] Stationary! Has officer but vx={transform.vx}, vy={transform.vy}")
            print(f"[SOLDIER {soldier_entity.id}] Formation pos: {unit.formation_position}")

    # Rest of update logic...
```

#### **B. Extend Command Radius**
```python
# File: game/formation.py - CommandInfluence class

INFLUENCE_RADIUS = {
    "general": 1000,   # Increased from 800
    "officer": 400,    # Increased from 300
    "soldier": 0
}
```

#### **C. Add "Rally Back" Behavior**
```python
# File: game/army_soldier_ai.py

def follow_formation(self, soldier_entity, officer, transform, unit, combat, dt):
    # Check distance to officer
    officer_transform = officer.get_component("Transform")
    if officer_transform:
        dx = officer_transform.x - transform.x
        dy = officer_transform.y - transform.y
        distance_to_officer = math.sqrt(dx*dx + dy*dy)

        # If too far from officer, RALLY BACK immediately
        if distance_to_officer > 350:  # Beyond effective command radius
            print(f"[SOLDIER RALLY] Soldier {soldier_entity.id} too far ({int(distance_to_officer)}), returning to officer")
            # Move directly toward officer, ignore formation position
            if distance_to_officer > 0:
                direction_x = dx / distance_to_officer
                direction_y = dy / distance_to_officer
                rally_speed = 150  # Faster than normal
                transform.vx = direction_x * rally_speed
                transform.vy = direction_y * rally_speed
                transform.x += transform.vx * dt
                transform.y += transform.vy * dt
            return  # Skip normal behavior

    # Normal formation following logic...
```

#### **D. Scout System Implementation**

**Scout Deployment Rules:**
```python
# File: game/army_ai.py - OfficerAI class

class ScoutSystem:
    def __init__(self, officer_ai):
        self.officer_ai = officer_ai
        self.scouts_deployed = []  # List of soldier entity IDs
        self.scout_positions = []  # Patrol positions
        self.max_scouts_percent = 0.10  # 10% max
        self.min_squad_for_scouts = 5  # Need at least 5 soldiers to send scouts

    def calculate_max_scouts(self, squad_size):
        """Calculate maximum number of scouts allowed"""
        if squad_size < self.min_squad_for_scouts:
            return 0  # No scouts if squad too small

        max_by_percent = int(squad_size * self.max_scouts_percent)
        return max(1, max_by_percent)  # Minimum 1 if allowed

    def should_deploy_scouts(self, threat_level, squad_size):
        """Decide if scouts should be deployed"""
        if squad_size < self.min_squad_for_scouts:
            return False

        # Deploy scouts when:
        # - Threat is unknown or low
        # - Not in active combat
        # - Squad has enough soldiers

        if threat_level in ["low", "medium"]:
            return True
        return False

    def assign_scout_positions(self, officer_position, base_position):
        """Calculate patrol positions around base perimeter"""
        positions = []
        num_scouts = len(self.scouts_deployed)

        if num_scouts == 0:
            return positions

        # Scouts patrol in circle around base
        # Radius = base_radius + 100 pixels
        base_radius = 100  # Default base radius
        patrol_radius = base_radius + 100

        for i in range(num_scouts):
            angle = (i / num_scouts) * 2 * math.pi
            x = base_position[0] + math.cos(angle) * patrol_radius
            y = base_position[1] + math.sin(angle) * patrol_radius
            positions.append((x, y))

        return positions

    def deploy_scouts(self, squad_soldiers, threat_level):
        """Deploy scouts from squad"""
        max_scouts = self.calculate_max_scouts(len(squad_soldiers))

        if max_scouts == 0 or not self.should_deploy_scouts(threat_level, len(squad_soldiers)):
            # Recall all scouts
            self.scouts_deployed = []
            return

        # Select soldiers for scouting
        self.scouts_deployed = squad_soldiers[:max_scouts]

        # Assign scout waypoints
        # (Will be used by soldier AI to patrol)
```

**Scout Behavior in Soldier AI:**
```python
# File: game/army_soldier_ai.py

def follow_formation(self, soldier_entity, officer, transform, unit, combat, dt):
    # Check if this soldier is assigned as scout
    if self.is_scout(soldier_entity):
        scout_position = self.get_scout_position(soldier_entity)
        if scout_position:
            self.patrol_scout_position(soldier_entity, scout_position, dt)
            return  # Skip formation following

    # Normal formation behavior...

def is_scout(self, soldier_entity):
    """Check if soldier is assigned to scouting duty"""
    # Query officer AI to see if this soldier is in scouts list
    # (Need to pass officer AI reference or use blackboard)
    return False  # Placeholder

def patrol_scout_position(self, soldier_entity, position, dt):
    """Patrol around assigned scouting position"""
    transform = soldier_entity.get_component("Transform")

    dx = position[0] - transform.x
    dy = position[1] - transform.y
    distance = math.sqrt(dx*dx + dy*dy)

    if distance > 20:  # Move to position
        direction_x = dx / distance
        direction_y = dy / distance
        scout_speed = 100
        transform.vx = direction_x * scout_speed
        transform.vy = direction_y * scout_speed
        transform.x += transform.vx * dt
        transform.y += transform.vy * dt
    else:  # At position, patrol in small circle
        # Simple patrol logic
        pass
```

### Scout System Visual Indicators
```python
# When rendering, scouts should have different sprite overlay
# - Small eye icon above sprite
# - Different color outline
# - Patrol path shown when F3 debug mode active
```

### Recommended Immediate Actions

**Priority 1 (Critical):**
1. Debug why soldiers aren't moving (add logging)
2. Extend officer command radius to 400
3. Add rally-back behavior for distant soldiers

**Priority 2 (Important):**
4. Implement scout system with limits
5. Add threat-based scout deployment

**Priority 3 (Polish):**
6. Visual indicators for scouts
7. Scout reporting to officer (enemy sightings)

---

## Implementation Order

### Phase 1: Critical Fixes ✅ COMPLETE
1. ✅ Fix enemy base capture (ownership mapping) - DONE
2. ✅ Fix soldier movement issues - DONE (rally-back behavior)
3. ✅ Implement general movement logic - DONE (repositioning triggers)
4. ✅ Add zoom controls - DONE (mouse wheel + keyboard)

### Phase 2: Tactical Systems ✅ COMPLETE
5. ✅ Combat vs capture priority system - DONE (exponential formula)
6. ✅ Rally-back behavior for distant soldiers - DONE (command radius enforcement)
7. ✅ Extend command radius - DONE (officer: 400, general: 1000)

### Phase 3: Advanced Features ✅ COMPLETE
8. ✅ Scout system with limits - DONE (10%, min 1 if 5+, passive patrol)
9. ⚠️ Scout visual indicators - NOT IMPLEMENTED (optional)
10. ⚠️ Polish and balance - ONGOING (tuning recommended)

---

## Testing Checklist

### General Movement
- [ ] General moves toward officer center of mass
- [ ] General stays behind front lines
- [ ] General responds to strategic changes
- [ ] Officers follow general when nearby

### Camera Zoom
- [ ] Mouse wheel zoom works
- [ ] +/- keys work
- [ ] Zoom transitions smoothly
- [ ] UI remains readable
- [ ] Performance acceptable when zoomed out

### Enemy Base Capture
- [ ] Enemy units reduce progress to 0.0
- [ ] Bases become enemy-owned (red) when progress < 0.3
- [ ] Enemy general targets player-owned bases
- [ ] Console shows enemy capture progress

### Combat Priority
- [ ] Units abandon early capture when threatened
- [ ] Units complete near-finished captures despite enemies
- [ ] Units retreat when overwhelmed
- [ ] Priority adjusts smoothly with capture progress

### Soldier Movement
- [ ] All soldiers assigned formation positions
- [ ] Soldiers move toward positions
- [ ] Soldiers rally back when too far
- [ ] No soldiers permanently stuck
- [ ] Scout limits enforced (10%, min 1, only if 5+ units)

---

## Balance Tuning Values

These values can be adjusted for gameplay feel:

```python
# Command Radii
OFFICER_INFLUENCE = 400  # Soldiers must stay within this
GENERAL_INFLUENCE = 1000  # Officers must stay within this

# Movement Speeds
SOLDIER_SPEED = 120
OFFICER_SPEED = 80
GENERAL_SPEED = 50

# Scout System
SCOUT_MAX_PERCENT = 0.10  # 10% of squad
SCOUT_MIN_SQUAD_SIZE = 5   # Need 5+ soldiers to scout
SCOUT_PATROL_RADIUS = 150  # Distance from base

# Priority Weights
CAPTURE_BASE_WEIGHT = 1.0
COMBAT_THREAT_HIGH = 1.5
RETREAT_OVERWHELMING = 2.0

# Capture Progress Bonuses
CAPTURE_75_PERCENT_BONUS = 2.5  # Very hard to pull units off
CAPTURE_50_PERCENT_BONUS = 2.0
CAPTURE_25_PERCENT_BONUS = 1.5
```

---

## Questions for User

Before implementing, please clarify:

1. **General Movement**: Should generals move actively, or reposition only when necessary?
2. **Zoom Levels**: Is 2 levels enough (1x and 0.5x), or want 3 levels (1x, 0.75x, 0.5x)?
3. **Scout Behavior**: Should scouts actively hunt enemies, or only observe and report?
4. **Combat Priority**: Should capture priority increase linearly or exponentially with progress?
5. **Performance**: How many total units on screen before zoom-out is required? (Currently targeting 60-80 units)

---

## End of Document
