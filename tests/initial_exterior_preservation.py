"""Narrow Milestone 3 projection for historical source comparisons.

No hashes/manifests are changed. Reverses startup additions/shared setup and the
explicit Ferrite cutover scene/discovery amendment; unrelated behavior stays pinned.
New startup methods have their own source contracts and deterministic fixtures.
"""


def without_initial_preparation(path, raw):
    # Exact approved cutover projection; all unrelated scene/progression bytes stay pinned.
    if path in ("scenes/world/planet_exterior.tscn", "scenes/main/playthrough_state.gd"):
        import re
        from current_preservation import git_blob
        original = git_blob('1dbdcbdc8a1ee22b411b5ded056d0a2574e1ff2a', path).decode('utf-8')
        current = raw.decode('utf-8').replace('\r\n', '\n')
        if path.endswith('.tscn'):
            expected = original.replace('load_steps=16', 'load_steps=13')
            expected = re.sub(r'^\[ext_resource[^\n]*(?:id="3_ferrite"|id="8_ferrite_art")[^\n]*\n', '', expected, flags=re.M)
            expected = re.sub(r'^\[sub_resource type="CircleShape2D" id="FerriteInspectionFootprint"\].*?(?=^; Grounded)', '', expected, flags=re.M | re.S)
            expected = re.sub(r'^\[node name="FerriteGround".*?(?=^\[node name="GroundObjects")', '', expected, flags=re.M | re.S)
            expected = re.sub(r'^\[node name="FerriteInspection".*?(?=^\[node name="CrashedShip")', '', expected, flags=re.M | re.S)
            assert current == expected, 'Unrelated exterior scene change'
        else:
            pattern = r'^func discover_ferrite\(.*?(?=^func recover_extractor)'
            assert re.sub(pattern, '', current, flags=re.M | re.S) == re.sub(pattern, '', original, flags=re.M | re.S)
            assert 'planet.resource_descriptor_v2_by_id(deposit_id, token)' in current
            assert 'if not starting:' in current
        return original.encode('utf-8')
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
        text = text.replace("var _startup_activation_pending: bool = false\n"
                            "var _startup_player_mode: Node.ProcessMode\n"
                            "var _startup_progression_mode: Node.ProcessMode\n"
                            "var _startup_state: PlanetWorldState\n"
                            "var _startup_seed: int\nvar _startup_revision: int\n", "", 1)
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
