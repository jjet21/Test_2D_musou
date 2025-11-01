# Movement & Capture Bug Fixes

## Issues Reported

1. **Squads stop moving after capturing an objective** despite other objectives remaining
2. **Generals and their squads don't move**
3. **Enemies can't seem to capture points**
4. **Units don't congregate to capture points** even with low/no threat, sometimes moving far away from bases

---

## Root Causes Identified

### Issue #1: Officers Stuck at Captured Objectives
**Problem:** Officers would reach a base, capture it, but then never look for a new target.
- Officer reaches within 100 pixels of target → stops moving
- Target position never cleared after capture
- No check for whether the current objective is already owned

**Root Cause:** Missing ownership check in `move_toward_objective()` (game/army_ai.py:597)

### Issue #2: Generals Not Moving
**Problem:** Generals only moved on specific repositioning triggers, which rarely fired during normal gameplay.
- Repositioning only triggered on: base loss, army shift >400px, or general >600px from army
- No continuous movement toward strategic objectives
- Generals would sit idle for long periods

**Root Cause:** General movement was trigger-only, no gradual advancement implemented

### Issue #3 & #4: Poor Capture Positioning
**Problem:** Units spread too far from base centers, sometimes outside capture radius entirely.
- CAPTURE_SPREAD formation used `spacing * 1.5 * sqrt(units)` formula
- For 10 units with spacing=75: radius = 355 pixels (WAY bigger than 100px base radius!)
- Officers stopped 100 pixels from target, which might be far from base center
- Target position not updated when close to base

**Root Cause:** Formation radius calculation didn't account for actual base size (game/formation.py:120)

---

## Fixes Applied

### Fix #1: Officer Objective Completion Check ✅
**File:** `game/army_ai.py` (lines 605-617)

Added check at start of `move_toward_objective()`:
```python
# CHECK: Is current objective already captured by our team?
if self.target_position and objective_system:
    target_x, target_y = self.target_position
    for base in objective_system.bases:
        dx = base.x - target_x
        dy = base.y - target_y
        if math.sqrt(dx*dx + dy*dy) < 50:  # This is our target base
            # Check if we already own it
            if base.owner == unit.team:
                print(f"[OFFICER {self.squad_id}] Objective {base.name} already captured! Looking for new target...")
                self.target_position = None
                break
```

**Effect:** Officers immediately recognize captured bases and look for new targets from strategic goals.

---

### Fix #2: Officer Target Validation ✅
**File:** `game/army_ai.py` (lines 619-630)

Enhanced fallback logic to verify targets aren't already owned:
```python
# FALLBACK: If no target assigned, look for strategic goal from blackboard
if not self.target_position:
    strategic_goal = self.blackboard.get_strategic_goal(unit.team)
    if strategic_goal and strategic_goal["target"]:
        target = strategic_goal["target"]
        # Only adopt target if we don't already own it
        if target.owner != unit.team:
            self.target_position = (target.x, target.y)
            self.current_order = strategic_goal["objective"]
            print(f"[OFFICER {self.squad_id}] Adopting strategic goal: {self.current_order} -> {target.name}")
        else:
            print(f"[OFFICER {self.squad_id}] Strategic target {target.name} already owned, waiting for new orders...")
```

**Effect:** Officers won't target bases they already own, forcing general to issue new strategic goals.

---

### Fix #3: General Continuous Movement ✅
**File:** `game/army_ai.py` (lines 72-74, 347-409)

Added `drift_toward_objective()` method called when not actively repositioning:
```python
# In update():
if self.target_position and transform:
    self.move_general_to_position(transform, dt)
else:
    # No active repositioning - gently drift toward strategic objective
    self.drift_toward_objective(entity_manager, transform, dt)
```

**New Method:**
- Calculates center of mass of officers
- Positions general 70% toward officers, 30% toward objective
- Only moves if >200 pixels from ideal position
- Speed: 30 (very slow, deliberate advance)

**Effect:** Generals now continuously advance with their army instead of sitting idle.

---

### Fix #4: Fixed Capture Formation Spread ✅
**File:** `game/formation.py` (lines 115-124)

Changed CAPTURE_SPREAD from dynamic scaling to fixed radius:
```python
# OLD:
capture_radius = spacing * 1.5 * math.sqrt(total_units)
# For 10 units: 355 pixels (too large!)

# NEW:
capture_radius = 70  # Fixed radius to fit within base capture zones
```

**Effect:** Units now spread at 70-pixel radius, fitting comfortably within 100-pixel base radius.

---

### Fix #5: Officer Base Center Positioning ✅
**File:** `game/army_ai.py` (lines 755-770)

Changed officer movement to always target base center when capturing:
```python
# OLD:
if base_distance > nearest_base.radius * 0.5:
    self.target_position = (nearest_base.x, nearest_base.y)
# Only updates if >50 pixels away

# NEW (for low threat):
self.target_position = (nearest_base.x, nearest_base.y)
# Always moves to center

# NEW (for medium/high threat):
if base_distance > nearest_base.radius * 0.3:
    self.target_position = (nearest_base.x, nearest_base.y)
# Still moves to center but with smaller threshold
```

**Effect:** Officers consistently move to base centers for optimal capture positioning.

---

### Fix #6: Reduced Stop Distance at Bases ✅
**File:** `game/army_ai.py` (lines 778-783)

Reduced stop distance when near bases:
```python
# OLD:
if distance < 100:  # Always stops at 100 pixels
    transform.vx = 0
    transform.vy = 0
    return

# NEW:
stop_distance = 30 if near_base else 100  # Get closer to base centers
if distance < stop_distance:
    transform.vx = 0
    transform.vy = 0
    return
```

**Effect:** Officers get within 30 pixels of base centers, ensuring optimal capture coverage.

---

## Testing Checklist

### Officers & Objectives
- [ ] Officers move to neutral bases
- [ ] Officers capture bases successfully
- [ ] Officers look for new targets after capturing
- [ ] Officers don't target already-owned bases
- [ ] Console shows "[OFFICER] Objective already captured!" messages

### Generals
- [ ] Generals drift slowly toward objectives
- [ ] Generals stay behind officer formations
- [ ] Generals reposition when triggered (base loss, army shift)
- [ ] Generals follow their armies

### Capture Behavior
- [ ] Units spread in circle at bases (not too far)
- [ ] Units remain within base capture radius (100 pixels)
- [ ] Officers get close to base centers (within 30 pixels)
- [ ] Multiple units inside capture zone
- [ ] Capture progress increases steadily

### Enemy Behavior
- [ ] Enemy generals issue orders
- [ ] Enemy officers move to player bases
- [ ] Enemy units attempt to capture
- [ ] Console shows enemy capture progress
- [ ] Bases change ownership to enemy (red) when captured

---

## Debug Visualization

**Keybind:** Press **F3** to toggle debug overlay

**Shows:**
- Command influence radii (officer: 400px, general: 1000px)
- Formation positions (yellow dots)
- Army statistics
- Unit counts and status

**Usage:**
- Verify officers are within command radius
- Check if soldiers have formation positions assigned
- See if capture spread is appropriate size
- Monitor threat levels and priorities

---

## Console Messages to Watch For

**Good Signs:**
```
[OFFICER team0_squad0] Adopting strategic goal: expand -> Center
[GENERAL TEAM 0] Strategy: expand, Target: Center at (1600, 1200)
[OFFICER team0_squad0] Objective Center already captured! Looking for new target...
[CAPTURE] Center: Team0=3.0 vs Team1=0.0, Progress=0.75
```

**Problem Signs:**
```
[OFFICER team0_squad0] Strategic target Center already owned, waiting for new orders...
# (Repeated many times = general not issuing new orders)

[CAPTURE] Center: Team0=0.5 vs Team1=0.0, Progress=0.75
# (Low capture power = units not close enough or too few)
```

---

## Summary of Changes

### Files Modified
1. **game/army_ai.py** - Officer and general movement logic
   - Added ownership check for objectives
   - Added general drift toward objectives
   - Fixed officer base center targeting
   - Reduced stop distance at bases

2. **game/formation.py** - Formation positioning
   - Fixed CAPTURE_SPREAD radius (355px → 70px)

### Compilation Status
✅ All files compiled successfully with no errors

---

## Expected Behavior After Fixes

1. **Continuous Movement:** Units constantly push toward objectives
2. **Objective Cycling:** After capturing, immediately look for next target
3. **Proper Capture Positioning:** Units cluster around base centers
4. **General Advancement:** Generals slowly follow their armies forward
5. **Enemy Participation:** Enemy armies actively capture and contest bases

The game should now feel more dynamic with armies constantly moving and contesting objectives!
