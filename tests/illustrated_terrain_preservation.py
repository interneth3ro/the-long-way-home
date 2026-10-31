"""Exact illustrated-lab inputs only; preserves every original terrain guard."""
import hashlib

INPUT_SHA256 = {
    'assets/experiments/native_terrain_47_96/illustrated_v1/.gitattributes': '733241eef1a5fec2b525d18fd22b2f23ec3b597185ae36d4ac42cf57c526f877',
    'assets/experiments/native_terrain_47_96/illustrated_v1/edge_compatibility.gdshader': '086cb2622360bbf2434427c3461cb8ae9468f7b8be9fade74b0140da9a9dd06f',
    'assets/experiments/native_terrain_47_96/illustrated_v1/illustrated_terrain.tres': '57df854e335b5d4354772e2449725ef5cda9229a7567d3befa7c50f08c66c096',
    'assets/experiments/native_terrain_47_96/illustrated_v1/mapping.json': 'f7367926ba4e90218da62de7a3ca4ff68e32f1b2039737c032a4c734e86f01b5',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/README.txt': 'ac3f2c34bf258ad64678c48ca70ba3d984b747000ccb4b2a573593fd2f376449',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/earth_solid.png': '1e530bdcefa9ba29575b8bd2c61a15ec26c04567b928ffebfb4b460336d4ff3f',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/green_solid.png': 'bc64176fde0d899dfd8c56d42a62fc81525e780c3b22687b982bde31244270e2',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/horizontal_earth_above.png': '2d0887c4d55456593cc66eca18c91b71af4eb51628e6c2b3de5b01ef6905b0ec',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/horizontal_green_above.png': 'd0226700f3cbb872ec5e29b18ef2d47b7257453c98748f7c0134f5af7dddcfaf',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/inner_earth_corner.png': '21c69334f8a1d3b5f99d0b6a95438dbc8dcfae12a06b9c35565643399fc57234',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/inner_green_corner.png': '5e6193c5dd44095ac9b64714df8391d1520d5668ed6385cc81686475f8d7359f',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/isolated_earth.png': '5c543fe2e8d543b007db3cce5ca618379826ac3b3d41c7067dec833381351dbc',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/isolated_green.png': 'e084699c8485ecf43884703c1485df740e833c22226ee85647684a0427241f40',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/narrow_earth_connection.png': '372ffaaeb61065dc01956300cf74021e0d1164368e4733077d17c76dadc0e628',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/narrow_green_connection.png': 'aad6e5f77cbf62861d191ea9bcd8cb2edf894dce39482c44eb514090300bc475',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/outer_earth_corner.png': '24659abe457529d329b1c00e8a9e6ff1ef70449261af259d1a7c3b9d4278bfa3',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/outer_green_corner.png': '866350b56a8a77a035065082cbd8739ad1998da6420efb755caefaef993851c5',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/vertical_earth_left.png': 'fe64065972619e9abeea811e3c270bd45a34e4430164eb86b9f84bb0c6e9eebf',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/vertical_green_left.png': '1ca2495f33aee5ff0fdac33764ea794956f64abc224274c5a55515290f8aacb0',
    'assets/experiments/native_terrain_47_96/illustrated_v1/unsupported_diagnostic.svg': 'b88891bf6cdbfcc2c2b11eb4beb949ded8e0dbe9cd46a652c87e28556c34aef4',
    'scenes/experiments/native_terrain_47_96/illustrated_v1.tscn': '35aa2d5e70f2dfb6ffe6d88c20875972fdb15310715c975c52f98e46d9d560a9',
}


def verify_input(path, raw):
    if path not in INPUT_SHA256:
        raise AssertionError(f"Unapproved illustrated input: {path}")
    if not path.endswith(".png"):
        raw = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256[path]:
        raise AssertionError(f"Modified illustrated input: {path}")
