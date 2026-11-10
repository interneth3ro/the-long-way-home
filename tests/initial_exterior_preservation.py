"""Narrow Milestone 3 projection for historical source comparisons.

No hashes/manifests are changed. Reverses only startup additions and shared setup
extraction; final comparisons still reject changes to all pre-existing behavior.
New startup methods have their own source contracts and deterministic fixtures.
"""


def without_initial_preparation(path, raw):
    if path not in ("scenes/world/planet_exterior.gd", "scenes/main/scene_transition_controller.gd"):
        return raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if path == "scenes/world/planet_exterior.gd":
        header = ("signal preparation_progress(completed: int, total: int)\n\n"
                  "const INITIAL_RADIUS: int = 3\nconst INITIAL_CHUNK_COUNT: int = 49\n\n")
        assert text.count(header) == 1
        text = text.replace(header, "", 1)
        start = text.index("\n\n# Shared setup uses the same generator")
        end = text.index("\n\n# Rechecked by the controller", start)
        setup = text.split("func _initialize_world(state: PlanetWorldState) -> void:\n", 1)[1].split(
            "\n\n# Player-independent startup contract", 1)[0]
        text = text[:start] + text[end:]
        assert text.count("\t_initialize_world(state)\n") == 1
        text = text.replace("\t_initialize_world(state)\n", setup, 1)
        text = text.replace("func _update_neighborhood(preparation_center: Variant = null) -> void:",
                            "func _update_neighborhood() -> void:", 1)
        text = text.replace("var center: Vector2i = preparation_center if preparation_center is Vector2i else \\\n\t\t"
                            "WorldCoordinates.world_to_chunk(to_local(_player.global_position))",
                            "var center := WorldCoordinates.world_to_chunk(to_local(_player.global_position))", 1)
    elif path == "scenes/main/scene_transition_controller.gd":
        text = text.replace("signal initial_preparation_progress(completed: int, total: int)\n", "", 1)
        text = text.replace("var _initial_generation: int = 0\nvar _initial_world: PlanetExterior\n"
                            "var initial_exterior_initialized: bool = false\n", "", 1)
        start = text.index("\n\n# MainV2 has finished synchronous interior spawn setup")
        end = text.index("\n\nfunc is_transitioning()", start)
        text = text[:start] + text[end:]
        text = text.replace("func _exit_tree() -> void:\n"
                            "\t# Staged children cancel their own work on exit; do not mutate exiting trees.\n"
                            "\t_initial_generation += 1\n\tinitial_exterior_initialized = false\n"
                            "\t_initial_world = null\n", "func _exit_tree() -> void:\n", 1)
    return text.encode("utf-8")


def verified_initial_paths():
    from pathlib import Path
    import subprocess
    root = Path(__file__).resolve().parents[1]
    paths = {"scenes/world/planet_exterior.gd", "scenes/main/scene_transition_controller.gd"}
    for path in paths:
        previous = subprocess.check_output(["git", "show", "5ab32bd:" + path], cwd=root)
        assert without_initial_preparation(path, (root / path).read_bytes()) == previous.replace(b"\r\n", b"\n"), path
    return paths
