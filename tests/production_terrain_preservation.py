"""Exact new PR #102 experiment inputs; no production or execution exemptions."""
import hashlib

FIXTURE_INPUT_SHA256 = {'scenes/experiments/production_terrain/engine_validation.gd': '35b7e0df6c35c37be24b937b2a655517bf13248755bde44e785fa0cec39c0073', 'scenes/experiments/production_terrain/fixture.gd': '7666b6751858e831592db429b1a7904b5200d5f1fc6f07daf158bd793b9476d4', 'scenes/experiments/production_terrain/fixture.tscn': 'a504f78a9aefae021ef297af949667b300ec46ab495a1361a8b000b454b9c22c', 'scenes/experiments/production_terrain/tint.gdshader': '212ddc3136cc4f8de6e6595ad45da465cbfa9e3a534a87105f9560c7c1c71b25'}


def verify_fixture_input(path, raw):
    if path not in FIXTURE_INPUT_SHA256:
        raise AssertionError('Unapproved fixture path: ' + path)
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != FIXTURE_INPUT_SHA256[path]:
        raise AssertionError('Modified fixture input: ' + path)
