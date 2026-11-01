"""Exact new PR #102 experiment inputs; no production or execution exemptions."""
import hashlib
from pathlib import Path
import subprocess
from exterior_activation_preservation import (
    ACTIVATION_INPUT_SHA256, historical_activation_bytes, verify_activation_input,
)

ROOT = Path(__file__).resolve().parents[1]
PRESENTER_BASE = '4c5bccc1877472a3551df756b673ef5e059dccf6'
# Exact PR #103 candidates only. Historical assertions still compare original
# bytes after candidate verification; no asset/directory/execution exemptions.
PRESENTER_INPUT_SHA256 = {
    'scenes/world/illustrated_terrain_presenter.gd': 'd569ff622464ff9db023cf39e8c4d7801df084c16d53e0b790add8bf2ef07935',
    'scenes/world/planet_exterior.gd': 'b422d1a21a0e840009123336c5a35067614deef614e92d4b9c4fea6fb92df804',
    'scenes/world/planet_exterior.tscn': 'dc693501865ecea78a4f93e40009955139e3016f9abbc1ee8606c0feca2f7b5d',
    'scenes/experiments/production_terrain/fixture.gd': 'f40bfe526e15a4a4197a7fce866b91c72fbbe9647119ee06e4cf49106373892c',
    'scenes/experiments/production_terrain/fixture.tscn': '6fe456e3a13c0275703b21c5a47091d7a61782c3b49bfabd004eb60645c3e47a',
    'scenes/experiments/production_terrain/engine_validation.gd': 'e900f3b525be3b8f83c87cb23761866cd91820c26048784558a3a533a5652abe',
}
PRESENTER_TEST_SHA256 = {
    'tests/static_weathered_earth_test.py': '8ef96278ac16b51738c404dd5d72b4c06af44c72a90fbbb4a0715e04590ebaf6',
    'tests/static_low_green_ground_test.py': 'ff9c1308fda5355ca480e639743bdfa1637bd50880deceb172ea24f093dae5a0',
    'tests/static_illustrated_terrain_test.py': '38a5309b6ce3997580079d977d9165f7d8674c29c8e285b2ccfa35393e4113bf',
    'tests/static_native_terrain_47_test.py': 'e79ebe9e297fc99a3237cefc08df762b37240b6954cdae0d66e71d00cb4abefa',
    'tests/static_machine_icons_test.py': '1d2a5da7cfbcbfa03c82c1b2e7e4229ee33b11779a4530c257a935840fc4357e',
    'tests/static_terrain_resolver_test.py': 'c7f7aa5f251bf4196d983ca906bf24580e90fc29e1a3870c0da71da490d435a6',
    'tests/static_production_terrain_test.py': '0c7ad461597cdfbe84aab076ce817f61b7001323cae59668e784a9d80204e48d',
    'tests/static_v2_production_host_test.py': '8c0dae93d9716a431987207e3e58879fc7e8b8ccae30fc681faf959b37e23c8d',
    'tests/static_v2_connection_test.py': '2df12d194936400879fcb73a3cec6ab9c32dadcd9b818e466cd267677ffd1a98',
}


def verify_presenter_input(path, raw):
    if path not in PRESENTER_INPUT_SHA256:
        raise AssertionError('Unapproved presenter path: ' + path)
    raw = historical_activation_bytes(path, raw)
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != PRESENTER_INPUT_SHA256[path]:
        raise AssertionError('Modified presenter input: ' + path)


def historical_presenter_bytes(path, raw):
    raw = historical_activation_bytes(path, raw)
    pins = PRESENTER_INPUT_SHA256 | PRESENTER_TEST_SHA256
    if path not in pins:
        return raw
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != pins[path]:
        raise AssertionError('Unreviewed PR #103 bytes: ' + path)
    return subprocess.check_output(['git', 'show', f'{PRESENTER_BASE}:{path}'], cwd=ROOT)


def historical_source(path):
    return historical_presenter_bytes(path, (ROOT/path).read_bytes()).decode().replace('\r\n', '\n')


def without_presenter_paths(paths):
    remaining = []
    for path in paths:
        if path in ACTIVATION_INPUT_SHA256:
            verify_activation_input(path, (ROOT/path).read_bytes())
        elif path in PRESENTER_INPUT_SHA256:
            verify_presenter_input(path, (ROOT/path).read_bytes())
        else:
            remaining.append(path)
    return remaining

FIXTURE_INPUT_SHA256 = {'scenes/experiments/production_terrain/engine_validation.gd': '35b7e0df6c35c37be24b937b2a655517bf13248755bde44e785fa0cec39c0073', 'scenes/experiments/production_terrain/fixture.gd': '7666b6751858e831592db429b1a7904b5200d5f1fc6f07daf158bd793b9476d4', 'scenes/experiments/production_terrain/fixture.tscn': 'a504f78a9aefae021ef297af949667b300ec46ab495a1361a8b000b454b9c22c', 'scenes/experiments/production_terrain/tint.gdshader': '212ddc3136cc4f8de6e6595ad45da465cbfa9e3a534a87105f9560c7c1c71b25'}


def verify_fixture_input(path, raw):
    if path not in FIXTURE_INPUT_SHA256:
        raise AssertionError('Unapproved fixture path: ' + path)
    raw = historical_presenter_bytes(path, raw)
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != FIXTURE_INPUT_SHA256[path]:
        raise AssertionError('Modified fixture input: ' + path)
