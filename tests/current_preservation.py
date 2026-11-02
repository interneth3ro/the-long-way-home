"""Current approved bytes before immutable historical guards; no engine execution.

Historical helpers, pins and manifests are deliberately left untouched. Only the
exact scoped candidates and individually pinned test edits below can be projected.
Everything else still reaches the original preservation guards. Audio candidate
receipts support static review; owner listening acceptance remains pending.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess

import exterior_activation_preservation as activation
import production_terrain_preservation as presenter
import native_terrain_preservation as native
import housekeeping_preservation as housekeeping
from ground_art_preservation import without_ground_art_paths, without_validation_changes

# Re-export immutable identities, never substitute current hashes for old pins.
from exterior_activation_preservation import (
    ACTIVATION_BASE, ACTIVATION_INPUT_SHA256, ACTIVATION_TEST_SHA256,
)
from production_terrain_preservation import (
    PRESENTER_BASE, PRESENTER_INPUT_SHA256, PRESENTER_TEST_SHA256,
    FIXTURE_INPUT_SHA256, verify_fixture_input,
)

ROOT = Path(__file__).resolve().parents[1]
# Hatch audio candidate only; no Native inventory or execution authorization.
# Historical PR #110/#112 receipts below remain unchanged.
AUDIO_BASE = 'ee75b8007de2bbefe73f192c971fd236872b810a'
AUDIO_INPUT_SHA256 = {
    'scenes/interaction/exterior_hatch_visual.gd': '915f11a2c0b4059557df5fdacb98fb450b02bb44be048ade3f2c700715e70bdc',
    'scenes/interaction/exterior_hatch_visual.tscn': '0d0acf585f14dd3f993597e3eb0c496ece2cffa1243eb48c32641ac4fab051fe',
    'scenes/interaction/exterior_hatch_audio.gd': '6f811bec85a3ff56fe46bf38079f12432a6846ce7b67bbb1fedd3d9cd859cdb2',
    'tools/generate-hatch-audio.py': 'd49e925fdfea691d5cd1044479d53b98c989e6ed9a24668cd8da2d292d92fa35',
    'assets/audio/exterior_hatch/hatch_open.wav': '20fe5cda88b672702f869921ad93a4c55f0906851b39142244a712ad13f13ea2',
    'assets/audio/exterior_hatch/hatch_close.wav': '17dee920be23e8d96848124ee8a3fbab4e9b3bca6895d929df840e35ae450b6f',
}
AUDIO_EXISTING_PATHS = {
    'scenes/interaction/exterior_hatch_visual.gd',
    'scenes/interaction/exterior_hatch_visual.tscn',
    'tests/static_exterior_boarding_test.py',
}
AUDIO_TEST_SHA256 = {
    'tests/static_exterior_boarding_test.py': 'ef01c636727637065b0b3e0ce6443b8052cddeaf29f84e305afe8de05a0a2b9a',
}

# PR #110's five exact production inputs. The original accepted hashes and
# sealed historical candidates below remain immutable. No directory exemption.
HATCH_BASE = '14876d26e4199922a5bd09cf436997792d7a5b6a'
HATCH_INPUT_SHA256 = {
    'scenes/world/planet_exterior.tscn': 'cd9f423e3711a13e968ec69c390e8a23484b4afbab1183745272a6eaae346d85',
    'scenes/interaction/exterior_hatch_visual.gd': 'a44154c7c798db799aadb5d22d84035388efac3e96e1727bde82dccef1a57a40',
    'scenes/interaction/exterior_hatch_visual.tscn': '5ff70e61445b29b185e99db7bf2c72418997a305ea24c7a954771635fa387042',
    'assets/environment/exterior/hatch_v2/door_leaf_opaque_v2.png': '7cccb9390beff971abd9e0f1c74455a35cf5b4cd05844f37887542ccea067e10',
    'assets/environment/exterior/hatch_v2/recess_backing_black_light.png': '80aa066edd98fae9eb5392ee79bb061bd82c80d48dc41e854e7c31141a3872c6',
}
# PR #112 exact reviewed deltas; historical pins above remain unchanged.
BOARDING_BASE = 'e4686cfb839eb7b205f56f28141541a318c4c94b'
BOARDING_INPUT_SHA256 = {
    'scenes/world/planet_exterior.tscn': '268fc13fb56d039f4ee9131f7e8d78031d3d300992d48c508524ce8b7c29682a',
    'scenes/world/planet_exterior.gd': '2c5f1a7f9cc39db58e0c76e8be8f3ae8d4caa5897c87f3fa30ae9b3bf8325f26',
    'scenes/interaction/exterior_hatch_visual.gd': '6f92b7d07f1d6fdff361989f2bb022bb70d21a22cb6a74a5a726da7f7105dbe7',
    'scenes/interaction/exterior_boarding.gd': 'e540b018cba6533193f921fb6aa5aab656c5ffb588a25122008733258f12b3b9',
}
BOARDING_TEST_SHA256 = {
    'tests/static_exterior_hatch_visual_test.py': '5696485b1fabcc678226ca7db4abe3bea63f423cf16310e591a851e08c7cfbc6',
    'tests/static_illustrated_exterior_test.py': 'd9806b87a38a4b462a31cbecee1b70cea2eafb3c782cc9fd1bb7ae92e314ba79',
}


ACCEPTED_IMPLEMENTATION = 'cb64ecacdf5dab5b76c26b8f3f765ce059f6e541'
MAINTENANCE_BASE = '5afaf66335a6dc4c7e1c2585c107ddeb91a1f8f2'
SEALED_REVIEW_HEAD = '4a364481e5eba90bba0d88b2518a8fce004dc979'
CURRENT_INPUT_SHA256 = {
    'scenes/main/scene_transition_controller.gd': '40bbb800b56b97254b929910af2a7bc1479baec08e902eefccd56c81d51e93ed',
    'scenes/player/follow_camera.gd': '77509b0a0729361c28e5fa0c3cc73b99a728a0f63b8c95b53ec64b0abd6ef844',
    'scenes/world/planet_exterior.tscn': '9359bc70d73d9d738c456c6d28169047370c4be1087512a7314d9a73f96acfd7',
    'assets/environment/exterior/crashed_exploration_ship_approved.png': '80ae633c36242c1effdcebea38dc05cfef8eb586ca9ef3103f6b02be91564e5b',
    'assets/environment/exterior/crashed_ship_contact_shadow_prototype.png': '1cd8111595e11d8beb527f538188f38f8517f1d3365633c013b9a137ca601777',
}
# The three owner-approved camera assertions added in the implementation also
# postdate older whole-tree guards. This is a new receipt, not an old pin edit.
ACCEPTED_TEST_SHA256 = {
    'tests/static_automatic_transitions_test.py': '9c6ff690c9a3d81674a62179b947764fbc07d586ab4ef3d9d11d49455c25c77d',
}
# Historical comparisons require the pre-camera controller/camera and the exact
# pre-ship PR #104 scene, not a rebaselined historical expected value.
PREDECESSORS = {
    'scenes/main/scene_transition_controller.gd': '029e1d54958d6259940cf44e4b5f56fb53bc0133',
    'scenes/player/follow_camera.gd': '029e1d54958d6259940cf44e4b5f56fb53bc0133',
    'scenes/world/planet_exterior.tscn': '061b9e24bd1a322a9acf0e45d07b5cb9b6450c31',
    'tests/static_automatic_transitions_test.py': '029e1d54958d6259940cf44e4b5f56fb53bc0133',
}
# New maintenance receipts only. Original test pins remain in their historical
# helpers. Each current test must match its complete reviewed bytes before the
# old helper sees its unchanged MAINTENANCE_BASE source.
MAINTAINED_TEST_SHA256 = {
    'tests/static_conversation_ui_test.py': 'c612404380686787ad30858f80f472e650fecc0d03cf26d2305ee26941ef0c64',
    'tests/static_ground_rejection_test.py': '5625c5b290f0754e9f40c5843b031e9bb0ff5522200e97613626f988fda53a8c',
    'tests/static_illustrated_exterior_test.py': 'bcb2bac3d365a22cd1562c818767603eace03149067e4c7ce6d7a47907bc7f83',
    'tests/static_illustrated_terrain_presenter_test.py': 'ff7cbcf7ffc0f6388d50c1c461200be03a9af1d486105a41f9943d6ccc5091a4',
    'tests/static_illustrated_terrain_test.py': 'a4722513a2d9f6effaf3019d84b16dcc536320a5c0953b867e9b12305b898e0b',
    'tests/static_low_green_ground_test.py': '5439e23cc9c1dd83fff92e08d12e0def50c79f9b9623ba48d04099f8ad7a59b0',
    'tests/static_machine_icons_test.py': '026f777f4e94bbafd45efc18204196d5350c0aa475ccf20d562f1814f863b3b3',
    'tests/static_musing_ui_test.py': 'd47af7d4ca07f251434cc9fa72d5fc3bdca4b605e40bfd4917c815e83ddd1a3f',
    'tests/static_native_terrain_47_test.py': '320b3adbd9631601433aee1594490c190dafeb928fc712f0b5ff6ca7dc48f33b',
    'tests/static_preservation_guards_test.py': 'c5b5b3b4764552d11508b67d9d34c61cbb904a7f45b2ed7d6a6426ef7bbaa155',
    'tests/static_production_terrain_test.py': 'cadfa5d4fc25c8bc47775c1fe7d5acc673391502a775356f94662e8f5b662397',
    'tests/static_terrain_resolver_test.py': '4b6274ffb9733fe0b0f5e2b9f1fd0a02a02320877088064bed86f48ce8358cc8',
    'tests/static_v2_connection_test.py': '5288ac3bf7ea0d8937324ed2692c61e64c1fc77a8f8a230341be73fecd9871f8',
    'tests/static_v2_production_host_test.py': '9c5b56d2a1ab48774788503189608558ef14599fc143b8b81dd39ed12c82f84a',
    'tests/static_weathered_earth_test.py': 'fc941691c00e9d3d0a7dadd6814764c190160592efa0d16515d3d93de5f22405',
}


def normalized(path, raw):
    return raw if path.endswith(('.png', '.wav')) else raw.replace(b'\r\n', b'\n')


@lru_cache(maxsize=None)
def git_blob(ref, path):
    # Read committed objects only; never check out, stage or execute them.
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=ROOT)


def verify_fingerprint(path, raw, digest, size=None):
    raw = normalized(path, raw)
    if hashlib.sha256(raw).hexdigest() != digest or (size is not None and len(raw) != size):
        raise AssertionError('Changed preserved input: ' + path)


def verify_current_input(path, raw):
    if path not in CURRENT_INPUT_SHA256:
        raise AssertionError('Unapproved current input: ' + path)
    raw = hatch_predecessor(path, raw)
    verify_fingerprint(path, raw, CURRENT_INPUT_SHA256[path])


def audio_predecessor(path, raw):
    """Validate exact audio candidates before comparing immutable predecessors."""
    raw = housekeeping.historical_input(path, raw)
    pins = AUDIO_INPUT_SHA256 | AUDIO_TEST_SHA256
    if path not in pins:
        return raw
    before = git_blob(AUDIO_BASE, path) if path in AUDIO_EXISTING_PATHS else None
    if before is not None and normalized(path, raw) == normalized(path, before):
        return before
    # Original PR #110 fixtures must still reach their original comparisons.
    if path == 'scenes/interaction/exterior_hatch_visual.gd':
        original = git_blob(BOARDING_BASE, path)
        if normalized(path, raw) == normalized(path, original):
            return original
    verify_fingerprint(path, raw, pins[path])
    return before if before is not None else raw


def boarding_predecessor(path, raw):
    """Validate complete boarding deltas before immutable PR #110 comparisons."""
    raw = audio_predecessor(path, raw)
    pins = BOARDING_INPUT_SHA256 | BOARDING_TEST_SHA256
    if path not in pins:
        return raw
    # New boarding script has no earlier representation.
    if path == 'scenes/interaction/exterior_boarding.gd':
        verify_fingerprint(path, raw, pins[path])
        return raw
    before = git_blob(BOARDING_BASE, path)
    if normalized(path, raw) == normalized(path, before):
        return before
    # Older historical fixtures still reach their original guards unchanged.
    if path == 'scenes/world/planet_exterior.tscn':
        for ref in (HATCH_BASE, PREDECESSORS[path]):
            if normalized(path, raw) == normalized(path, git_blob(ref, path)):
                return raw
    verify_fingerprint(path, raw, pins[path])
    return before


def hatch_predecessor(path, raw):
    """Validate the complete visual-only scene before older comparisons run."""
    raw = boarding_predecessor(path, raw)
    if path != 'scenes/world/planet_exterior.tscn':
        return raw
    before = git_blob(HATCH_BASE, path)
    if normalized(path, raw) == normalized(path, before):
        return raw
    # Pre-existing historical fixtures must still reach their original guards.
    historical = git_blob(PREDECESSORS[path], path)
    if normalized(path, raw) == normalized(path, historical):
        return raw
    verify_fingerprint(path, raw, HATCH_INPUT_SHA256[path])
    return before


def historical_bytes(path, raw):
    """Validate a complete approved delta before returning its original bytes."""
    raw = housekeeping.historical_input(path, raw)
    raw = hatch_predecessor(path, raw)
    pins = CURRENT_INPUT_SHA256 | ACCEPTED_TEST_SHA256 | MAINTAINED_TEST_SHA256
    if path not in pins:
        return raw
    predecessor = PREDECESSORS.get(path)
    if path in MAINTAINED_TEST_SHA256:
        predecessor = MAINTENANCE_BASE
    before = git_blob(predecessor, path) if predecessor else None
    # Existing guards deliberately also exercise their original inputs.
    if before is not None and normalized(path, raw) == normalized(path, before):
        return before
    verify_fingerprint(path, raw, pins[path])
    return before if before is not None else raw


def historical_text(path, text):
    return historical_bytes(path, text.encode('utf-8')).decode('utf-8').replace('\r\n', '\n')


def historical_activation_bytes(path, raw):
    return activation.historical_activation_bytes(path, historical_bytes(path, raw))


def verify_activation_input(path, raw):
    activation.verify_activation_input(path, historical_bytes(path, raw))


def historical_presenter_bytes(path, raw):
    return presenter.historical_presenter_bytes(path, historical_bytes(path, raw))


def verify_presenter_input(path, raw):
    presenter.verify_presenter_input(path, historical_bytes(path, raw))


def historical_source(path):
    return historical_presenter_bytes(path, (ROOT/path).read_bytes()).decode('utf-8').replace('\r\n', '\n')


def historical_test_bytes(path, raw):
    # The original PR #98 self-test explicitly supplies its pre-amendment bytes.
    # Preserve that exact immutable case as well as the latest reviewed edit.
    if path in native.TEST_UPDATE_SHA256:
        original = git_blob(native.REVIEWED_HEAD, path)
        if normalized(path, raw) == normalized(path, original):
            return native.historical_test_bytes(path, raw)
    return native.historical_test_bytes(path, historical_bytes(path, raw))


def without_current_paths(paths):
    # Verify all five complete authorized validation edits before the unchanged
    # Stage 2A comparison sees its remaining historical inputs.
    paths = without_validation_changes(paths)
    paths = without_ground_art_paths(paths)
    paths = housekeeping.without_approved_paths(paths)
    remaining = []
    for path in paths:
        if path in AUDIO_INPUT_SHA256:
            audio_predecessor(path, (ROOT/path).read_bytes())
        elif path in CURRENT_INPUT_SHA256:
            verify_current_input(path, (ROOT/path).read_bytes())
        elif path in BOARDING_INPUT_SHA256:
            verify_fingerprint(path, (ROOT/path).read_bytes(), BOARDING_INPUT_SHA256[path])
        elif path in HATCH_INPUT_SHA256:
            verify_fingerprint(path, boarding_predecessor(path, (ROOT/path).read_bytes()), HATCH_INPUT_SHA256[path])
        else:
            remaining.append(path)
    return remaining


def without_presenter_paths(paths):
    # Exact five paths AND hashes; no tree, extension or execution exemptions.
    return presenter.without_presenter_paths(without_current_paths(paths))


def sealed_input(path, record):
    raw = git_blob(SEALED_REVIEW_HEAD, path)
    verify_fingerprint(path, raw, record['sha256'], record['bytes'])
    return normalized(path, raw)
