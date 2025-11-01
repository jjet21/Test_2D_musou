# Priority System Implementation

## Overview

Implemented a comprehensive priority system that governs:
1. **Objective selection** - Distance-weighted strategic targeting
2. **Combat targeting** - Rank-based enemy prioritization
3. **Protection behavior** - Rank-based ally protection

All priorities respect team membership - units only protect same-team allies and only target opposite-team enemies.

---

## Problem #1: Base Capture Visualization ✅ FIXED

### Issue
When red team captured bases, the progress bar appeared empty instead of filling with red.

### Root Cause
Progress bar only showed one direction (blue team progress from 0.0 to 1.0).

### Fix (main.py:453-497)
Implemented bi-directional progress bar:
- **Left half**: Red (team 1) fills when progress < 0.5
- **Right half**: Blue (team 0) fills when progress > 0.5
- **Center line**: White line marks neutral point (0.5)

```python
if base.capture_progress < 0.5:
    # Red capturing - fill leftward from center
    red_progress = (0.5 - base.capture_progress) * 2
    red_width = int((progress_width // 2) * red_progress)
    # Draw red bar from center leftward
elif base.capture_progress > 0.5:
    # Blue capturing - fill rightward from center
    blue_progress = (base.capture_progress - 0.5) * 2
    blue_width = int((progress_width // 2) * blue_progress)
    # Draw blue bar from center rightward
```

**Result:** Red progress now visually fills left, blue fills right, making capture status clear.

---

## Problem #2: Distance Not Factored Into Objective Importance ✅ FIXED

### Issue
Generals would pick high-value objectives regardless of distance, causing units to run across the entire map while ignoring closer bases.

### Root Cause
`choose_target_objective()` only considered strategic value, not distance.

### Fix (game/army_ai.py:133-219)

Added distance-based scoring:

```python
def choose_target_objective(self, objective_system, strategy, entity_manager):
    # Calculate army center of mass
    army_center_x, army_center_y = self._calculate_army_center(entity_manager)

    # Score each base
    def score_base(base):
        strategic_value = self.objective_priorities.get(base.name, 1.0)

        # Calculate distance from army center to base
        distance = math.sqrt((base.x - army_center_x)**2 + (base.y - army_center_y)**2)
        distance_factor = (distance / 1000.0) + 0.5

        # Score = strategic_value / distance_factor
        # Higher value = better, closer = better
        return strategic_value / distance_factor

    # Sort by score (highest first)
    bases = sorted(bases, key=score_base, reverse=True)
    return bases[0]
```

**Scoring Examples:**
- High-value (1.5x) close base (500px): 1.5 / 1.0 = **1.5 score**
- Normal (1.0x) very close base (100px): 1.0 / 0.6 = **1.67 score** ← Wins!
- High-value (1.5x) distant base (2000px): 1.5 / 2.5 = **0.6 score**

**Result:** Generals now prefer closer objectives unless distant ones are significantly more valuable.

---

## Problem #3: No Rank-Based Combat Priorities ✅ FIXED

### Issue
Soldiers treated all enemies equally - would attack random grunts while enemy generals walked past unchallenged.

### Requirements
1. Killing general > officer > soldier
2. Protecting general > officer > self
3. Squad relationships matter (your officer > other officers)
4. Team-specific (blue soldiers don't defend red officers)

### Fix (game/army_soldier_ai.py:154-267)

Implemented `select_priority_target()` with 3-tier priority system:

#### **PRIORITY 1: Protect Friendly Commanders** (Highest)

```python
# Check if OUR GENERAL is threatened
generals = [e for e in entity_manager.get_entities_with_tag("general")
           if e.active and e.has_tag(f"team_{friendly_team}")]  # TEAM CHECK!

for general in generals:
    for enemy in nearby_enemies:
        # Enemy within 200px of our general = threat!
        if distance_to_general < 200:
            print("[PROTECTION] Soldier protecting general!")
            return enemy  # Attack this enemy immediately

# Check if OUR SQUAD'S OFFICER is threatened
squad_info = blackboard.get_squad_info(unit.squad_id)
officer_id = squad_info["officer_id"]  # OUR officer specifically

for enemy in nearby_enemies:
    # Enemy within 150px of our officer = threat!
    if distance_to_officer < 150:
        print("[PROTECTION] Soldier protecting officer!")
        return enemy  # Attack this enemy immediately
```

**Protection radii:**
- General: 200 pixels
- Officer: 150 pixels

**Team verification:** Only protects units with matching `team` tag.

---

#### **PRIORITY 2: Target High-Rank Enemies** (Medium)

```python
rank_scores = {
    "general": 3.0,   # 3x priority
    "officer": 2.0,   # 2x priority
    "soldier": 1.0    # 1x priority (baseline)
}

def target_score(enemy_tuple):
    enemy, dist, rank, _ = enemy_tuple
    rank_score = rank_scores.get(rank, 1.0)
    distance_factor = (dist / 100.0) + 0.5

    # Score = rank_value / distance_factor
    return rank_score / distance_factor

# Sort enemies by score (highest first)
nearby_enemies.sort(key=target_score, reverse=True)
return nearby_enemies[0]  # Best target
```

**Scoring Examples:**
- General at 100px: 3.0 / 1.5 = **2.0 score** ← High priority!
- Officer at 50px: 2.0 / 1.0 = **2.0 score** ← Also high!
- Soldier at 50px: 1.0 / 1.0 = **1.0 score**
- General at 500px: 3.0 / 5.5 = **0.55 score**

**Result:** Soldiers preferentially target high-rank enemies, but distance still matters.

---

#### **PRIORITY 3: Nearest Enemy** (Fallback)

If no commanders are threatened and no enemies in detection range, returns `(None, inf)`.

---

### Detection Range

```python
detection_range = combat.attack_range * 4  # Can see enemies 4x attack range away
```

Soldiers scan a wider area than their attack range to spot threats to commanders early.

---

### Team Verification Throughout

**Every check includes team verification:**

```python
# Protection: only protect same-team units
friendly_tag = f"team_{unit.team}"
generals = [e for e in entity_manager.get_entities_with_tag("general")
           if e.active and e.has_tag(friendly_tag)]  # ← TEAM CHECK

# Targeting: only target opposite-team units
enemy_team = 1 - unit.team
enemy_tag = f"team_{enemy_team}"
enemies = [e for e in entity_manager.get_entities_with_tag(enemy_tag)
          if e.active]  # ← TEAM CHECK
```

**Result:** Blue soldiers never defend red officers, red soldiers never defend blue generals.

---

## Priority System in Action

### Example Scenario

**Blue soldier's perspective:**
1. Blue general is 300px away, safe
2. Blue officer (my squad) is 80px away, safe
3. Enemy soldier is 50px away
4. Enemy officer is 150px away
5. Enemy general is 300px away

**Priority calculations:**

**Protection checks:**
- Blue general safe (no enemies within 200px)
- Blue officer safe (no enemies within 150px)
- ✗ No protection needed

**Offense scores:**
| Enemy | Rank | Distance | Score | Calculation |
|-------|------|----------|-------|-------------|
| Enemy general | 3.0 | 300px | **0.86** | 3.0 / (3.5) |
| Enemy officer | 2.0 | 150px | **0.95** | 2.0 / (2.0) |
| Enemy soldier | 1.0 | 50px | **1.0** | 1.0 / (1.0) ← **WINNER** |

**Result:** Attacks closest enemy soldier.

---

### Example Scenario (Protection Triggered)

**Blue soldier's perspective:**
1. Enemy officer is 120px from my squad's officer
2. Enemy soldier is 30px from me

**Priority calculations:**

**Protection checks:**
- Blue general safe
- Blue officer THREATENED! (enemy officer within 150px)
- ✓ **Protection triggered!**

**Result:** Immediately attacks enemy officer threatening my officer, ignoring the closer enemy soldier.

---

## Console Messages

When protection activates, you'll see:

```
[PROTECTION] Soldier protecting general from officer!
[PROTECTION] Soldier protecting officer from soldier!
```

These messages indicate the priority system is working correctly.

---

## Summary of Changes

### Files Modified

1. **main.py** (lines 453-497)
   - Bi-directional base capture progress bar

2. **game/army_ai.py** (lines 133-219)
   - Distance-weighted objective selection
   - `_calculate_army_center()` helper method

3. **game/army_soldier_ai.py** (lines 154-267, 341-348)
   - `select_priority_target()` method
   - Protection priority system
   - Rank-based targeting
   - Team verification throughout

### Compilation Status
✅ All files compiled successfully with no errors

---

## Testing Guide

### Test Protection Behavior
1. Watch soldiers near their officer/general
2. When enemies approach commanders, soldiers should disengage from current targets
3. Console shows: `[PROTECTION] Soldier protecting X from Y!`

### Test Rank Targeting
1. Place enemy general, officer, and soldiers at similar distances
2. Blue soldiers should preferentially target the general
3. If general is much farther, may target closer officer/soldier

### Test Distance-Weighted Objectives
1. Create bases at various distances with different strategic values
2. Generals should prefer closer bases unless distant ones are very high value
3. Console shows: `[GENERAL] Strategy: expand, Target: <base_name>`

### Test Team Verification
1. Blue soldiers should NEVER show protection messages for red units
2. Red soldiers should NEVER show protection messages for blue units
3. Each team only targets opposite-team enemies

---

## Tuning Parameters

All values are easily adjustable:

| Parameter | Value | Location | Purpose |
|-----------|-------|----------|---------|
| General protection radius | 200px | army_soldier_ai.py:213 | Range to protect general |
| Officer protection radius | 150px | army_soldier_ai.py:243 | Range to protect officer |
| General rank score | 3.0 | army_soldier_ai.py:253 | General target priority |
| Officer rank score | 2.0 | army_soldier_ai.py:253 | Officer target priority |
| Soldier rank score | 1.0 | army_soldier_ai.py:253 | Soldier target priority |
| Detection range multiplier | 4x | army_soldier_ai.py:168 | How far soldiers scan |
| Distance normalization | 1000 | army_ai.py:175 | Objective distance scaling |

---

## Expected Behavior

1. **Base visualization**: Red fills left, blue fills right, clear progress indication
2. **Smart objective selection**: Armies prefer nearby bases unless distant ones are much more valuable
3. **Bodyguard behavior**: Soldiers immediately defend threatened commanders
4. **Rank-aware combat**: Units preferentially target high-rank enemies
5. **Squad loyalty**: Soldiers protect their own officer first
6. **Team-specific**: All behaviors respect team membership

The tactical depth should now be significantly enhanced with units making intelligent decisions about targets and protection!
