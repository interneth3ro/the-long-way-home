# The Long Way Home

A story-driven science-fiction automation adventure. This fresh Godot project
has a playable walkable-ship greybox on this feature branch (pending merge).
Dave can explore three connected bays with collision and a following camera.
It is independent of the previous FactoryGame project.

## Requirements and setup

- Godot **4.7.2 stable**, standard build. GDScript is the initial scripting language;
  no .NET SDK or third-party plugins are required.
- Git for cloning the repository.

```sh
git clone https://github.com/interneth3ro/the-long-way-home.git
cd the-long-way-home
godot --editor --path .
```

`godot` denotes your Godot executable; use its full path if it is not on `PATH`.
Alternatively, import `project.godot` through Godot's Project Manager.

## Launch and validation

Press **F6** with `scenes/main/main.tscn` open, or **F5** to run the project.
From a terminal in the project root:

```sh
godot --path .
godot --headless --editor --path . --quit
godot --headless --path . --quit-after 60
```

The last two commands validate editor import and a bounded main-scene launch.
Headless checks do not verify graphical appearance. Run the focused regression checks:

```sh
godot --headless --path . --script tests/ship_foundation_test.gd
```

They exercise real physics movement, normalized diagonals, wall sliding, obstacles,
doorways, hull boundaries, camera follow and limits, zoom, and replacing Dave's
visual child. Graphical validation remains a separate check.

## Controls and greybox conventions

- Move: **WASD** or **arrow keys** (`move_left/right/up/down`).
- Zoom out/in: hold **Q / E** or **- / =** (`zoom_out/in`).
- Dave moves at 220 world units per second; diagonal input is normalized.
- Physics runs at 120 ticks per second with interpolation; the camera updates
  with physics. Rendering is capped at 120 FPS with V-sync disabled to reduce
  presentation latency. This can cause tearing on some displays.
- Zoom normally ranges from 0.85 to 1.4, starting at 1.1. The camera clamps to
  the 1600 by 1000 room. On oversized viewports the minimum zoom increases to
  keep the room filling the view; this can override the normal maximum.

Godot coordinates are positive X right and positive Y down. Dave's origin is his
foot/ground contact point, with a 24 by 20 capsule footprint and a roughly
24 by 53 placeholder silhouette extending upward. Replace the `Visual` child
with artwork anchored at local (0, 0); movement and collision do not reference it.
The camera is a sibling of `Visual`, so artwork replacement preserves following.
Doorway openings are 180 world units wide. These are greybox proportions, not a
final construction grid or production art specification.

Floor decorations draw first. Dave and static obstacles share `Actors` Y-sorting;
obstacle origins sit at their footprint's bottom edge. Raised faces extend upward
from that sorting anchor. This allows Dave to pass behind and in front of props.
The HUD is on a separate `CanvasLayer`.

The layout and colors are temporary. There are no interactive doors, dialogue,
objectives, narrative state, saves, machinery, or research systems. Approved art
and narrative direction remains in [GAME_VISION](docs/GAME_VISION.md).

## Layout and development

- `project.godot`: engine settings and main-scene entry point.
- `scenes/main/main.tscn`: handcrafted three-bay interior, static collision,
  ground decorations, Y-sorted actors, and a screen-space controls label.
- `scenes/player/dave.tscn`: reusable foot-anchored Dave with independent
  `Visual`, `FootCollision`, and following `Camera2D` children.
- `scripts/dave.gd`: physics movement; `scripts/ship_camera.gd`: bounded zoom.
- `tests/ship_foundation_test.gd`: headless behavior regression checks.
- `docs/GAME_VISION.md`: approved direction and unresolved design questions.
- `AGENTS.md`: development conventions.

Add feature directories and GDScript files when they have a concrete purpose.
Keep Godot's `.godot/` cache untracked. Use feature branches and pull requests;
validate affected scenes and scripts before requesting review.

Keep authoritative documentation in `docs/` and generated evidence out of Git;
the artifact retention and ZIP policies are in [AGENTS.md](AGENTS.md).
Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
review. After an approved merge, separately request
[post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) for that PR number
from a chat attached to a surviving checkout. Cleanup stops when preservation,
attachment or Windows lock safety cannot be verified.
