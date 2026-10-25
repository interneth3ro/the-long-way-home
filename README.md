# The Long Way Home

A story-driven science-fiction automation adventure. This fresh Godot project
currently contains only a title scene and project documentation; no gameplay is
implemented. It is independent of the previous FactoryGame project.

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
Headless checks do not verify graphical appearance.

## Layout and development

- `project.godot`: engine settings and main-scene entry point.
- `scenes/main/main.tscn`: minimal title scene.
- `docs/GAME_VISION.md`: approved direction and unresolved design questions.
- `AGENTS.md`: development conventions.

Add feature directories and GDScript files when they have a concrete purpose.
Keep Godot's `.godot/` cache untracked. Use feature branches and pull requests;
validate affected scenes and scripts before requesting review.
