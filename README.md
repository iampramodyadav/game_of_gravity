# 🌌 Gravity Puzzle - Second-Order Mechanics Game

A physics-based puzzle game where you don't control the character—you control the laws of physics themselves. Manipulate gravity direction and air density to guide a ball through increasingly challenging levels filled with hazards and obstacles.

![Game Genre](https://img.shields.io/badge/Genre-Physics%20Puzzle-blue)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-Proprietary-red)

## 🎮 Game Concept

**Second-Order Mechanics** - Instead of directly controlling the player ball, you manipulate the environment's physics constants:
- **Gravity Direction**: Change which way gravity pulls (up, down, left, right)
- **Air Density**: Adjust drag/damping to control ball momentum

This creates a unique puzzle experience where planning and physics understanding are key to success.

## ✨ Features

### Core Gameplay
- 🎯 **20 Handcrafted Levels** across 4 difficulty tiers
- 💀 **Lives System** with hazard-based respawning
- ⏱️ **Time-Based Scoring** - faster completions earn higher scores
- 🎨 **Dynamic Particle Effects** - visualize air density and physics
- 💾 **Auto-Save Progress** - never lose your achievements

### Menu System
- **Main Menu** - Clean, modern interface
- **Level Select** - Visual grid showing all levels with unlock status
- **Statistics** - Track total playtime, deaths, and completion
- **Pause Menu** - Resume, restart, or quit mid-level

### Visual Polish
- Animated pulsing hazards and goals
- Particle trail system (color-coded to air density)
- Explosion effects on death
- Victory particle bursts
- Decorative spike elements on hazards

## 🕹️ Controls

| Key | Action |
|-----|--------|
| **Arrow Keys** | Change gravity direction (↑↓←→) |
| **W** | Increase air density (more drag) |
| **S** | Decrease air density (less drag) |
| **R** | Restart current level |
| **ESC** | Pause/Resume game |

## 📊 Difficulty Levels

- 🟢 **Easy** (Levels 1-4): 3-5 lives, gentle introduction
- 🟡 **Medium** (Levels 5-8): 3 lives, complex navigation
- 🔴 **Hard** (Levels 9-12): 2-3 lives, precision required
- 🟣 **Insane** (Levels 13-20): 1-2 lives, master-level challenges

## 🛠️ Technical Details

### Built With
- **Python 3.8+**
- **Pygame** - Graphics and game loop
- **Pymunk** - 2D physics engine
- **JSON** - Level data and save system

### Project Structure
```
gravity-puzzle/
├── main.py           # Main game engine
├── levels.json       # Level definitions
├── save_data.json    # Player progress (auto-generated)
└── README.md         # This file
```

### Level Data Format
Each level in `levels.json` contains:
```json
{
    "level_id": 1,
    "name": "Tutorial",
    "difficulty": "easy",
    "lives": 5,
    "start_pos": [100, 300],
    "gravity_start": [0, 900],
    "damping_start": 0.9,
    "goal_rect": [700, 250, 50, 100],
    "walls": [[x, y, width, height], ...],
    "hazards": [[x, y, width, height], ...]
}
```

## 🚀 Installation & Running

### Prerequisites
```bash
pip install pygame pymunk
```

### Run the Game
```bash
python main.py
```

### System Requirements
- Python 3.8 or higher
- 2GB RAM minimum
- Works on Windows, macOS, and Linux

## 🎯 Game Mechanics Deep Dive

### Gravity Control
- Gravity applies constant force in chosen direction (900 units by default)
- Instant switching allows for mid-air direction changes
- Strategic gravity flips are essential for complex levels

### Air Density (Damping)
- Range: 0.1 (thin air, high speed) to 1.0 (thick air, slow motion)
- Higher damping = more control but slower movement
- Lower damping = faster but harder to control
- Visual feedback via particle trail colors

### Hazards
- Red pulsing zones with decorative spikes
- Instant death on contact (costs one life)
- Respawn at level start if lives remain
- Game over returns to main menu

### Scoring
- Formula: `Score = 10,000 - (time_in_frames × 10)`
- Faster completion = higher score
- Best score saved per level
- Encourages both completion and speed

## 🏆 Progression System

- Levels unlock sequentially
- Must complete Level N to unlock Level N+1
- Progress auto-saves after each completion
- Statistics track overall performance
- Level select allows replaying any unlocked level

## 📝 Save Data

Game automatically saves to `save_data.json`:
```json
{
    "unlocked_levels": 5,
    "level_scores": {
        "1": 9850,
        "2": 9200
    },
    "total_time": 324.5,
    "total_deaths": 12
}
```

## 🎨 Design Philosophy

This game explores **second-order game mechanics** where player agency is one step removed from direct control. Rather than moving the character, you reshape the world's rules. This creates:

1. **Puzzle-like thinking** - Planning required before acting
2. **Physics intuition** - Understanding momentum and forces
3. **Creative solutions** - Multiple ways to solve levels
4. **Skill progression** - Mastery through physics understanding

## 🐛 Known Issues

- None currently reported

## 🔮 Future Enhancements (Potential)

- Level editor for custom levels
- Online leaderboards
- More physics variables (elasticity, friction)
- Replay system
- Additional particle effects

## 📜 License & Usage Rights

**© 2024 - All Rights Reserved**

This project is **proprietary software**. 

### ⚠️ Usage Restrictions

**NO PERMISSION IS GRANTED** for any of the following without explicit written authorization:

- ❌ Copying, forking, or cloning this repository
- ❌ Using any code, assets, or concepts in other projects
- ❌ Distributing or sharing the game or its source code
- ❌ Creating derivative works or modifications
- ❌ Commercial or non-commercial use
- ❌ Public display or performance

**This code is provided for portfolio/demonstration purposes only.**

### 📧 Contact for Permissions

If you wish to use any part of this project, you **must** obtain written permission first.

**Unauthorized use, reproduction, or distribution is strictly prohibited and may result in legal action.**

---

## 👨‍💻 Developer

Created as a personal project exploring second-order game mechanics and physics-based puzzle design.

**This is proprietary software - all rights reserved.**

---

### 🎮 Game Philosophy

*"The best puzzle games don't give you direct control—they give you the rules and ask you to think."*

This game represents an exploration of indirect control schemes and emergent gameplay through physics manipulation. Every level is solvable, but the path requires understanding momentum, timing, and strategic use of environmental forces.

---

**Repository Status**: Private / Portfolio Demonstration  
**Playability**: Fully functional game with 20 complete levels  
