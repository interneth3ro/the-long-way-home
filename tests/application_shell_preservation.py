"""Exact startup amendment for older milestone preservation comparisons."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APPLICATION_FILES = {
    "scenes/application/loading_screen.gd",
    "scenes/application/loading_screen.tscn",
    "scenes/application/application.gd",
    "scenes/application/application.gd.uid",
    "scenes/application/application.tscn",
    "scenes/application/title_background.tscn",
    "scenes/application/title_screen.gd",
    "scenes/application/title_screen.gd.uid",
    "scenes/application/title_screen.tscn",
    "scenes/application/pause_menu.gd",
    "scenes/application/pause_menu.gd.uid",
    "scenes/application/pause_menu.tscn",
}
LOADING_SCREEN_UID = "scenes/application/loading_screen.gd.uid"


def verify_loading_screen_uid(raw):
    """PR #175's exact identity; no other UID path or content is exempted."""
    assert raw.replace(b"\r\n", b"\n") == b"uid://cqbd6damin78b\n", "Approved loading-screen UID changed"
    return {LOADING_SCREEN_UID}


def without_application_startup(raw):
    current = b'run/main_scene="res://scenes/application/application.tscn"'
    previous = b'run/main_scene="res://scenes/main/main_v2.tscn"'
    assert raw.count(current) == 1 and previous not in raw
    return raw.replace(current, previous, 1)


def verified_application_paths():
    baseline = subprocess.check_output([
        "git", "show", "1f6c128ad1a77fa103ab6c2a260411d6bcd30420:project.godot"
    ], cwd=ROOT)
    actual = without_application_startup((ROOT / "project.godot").read_bytes())
    assert actual.replace(b"\r\n", b"\n") == baseline.replace(b"\r\n", b"\n")
    uid = verify_loading_screen_uid((ROOT / LOADING_SCREEN_UID).read_bytes())
    return APPLICATION_FILES | {"project.godot"} | uid
