# Development conventions

- Favor small, independently testable changes; stay within the requested scope.
- Separate gameplay simulation, presentation, and narrative state.
- Avoid speculative abstractions and unnecessary managers.
- Maintain stable, clearly defined interfaces.
- Keep narrative content independently editable.
- Validate Godot scenes and scripts before reporting completion. Run headless
  editor import and the main scene; distinguish headless from graphical checks.
- Do not commit Godot-generated caches or temporary test artifacts.
- Do not introduce third-party plugins without approval.
- Do not begin unrelated development or access or modify the previous FactoryGame
  project. This is a fresh implementation; do not reuse its files or architecture.
- Use feature branches and pull requests for future development; do not rewrite
  existing history or merge without authorization.
- Preserve user-authored artwork, saves, settings, and other project data.
- Never perform destructive cleanup without verifying ownership and preservation
  requirements.
