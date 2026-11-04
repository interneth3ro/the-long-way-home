extends Node2D
## Fixed visual experiment. No production presenter, state, streaming or writes.
const Metadata = preload("res://scenes/world/continuous_terrain_metadata.gd")
const LAB_SHADER = preload("res://scenes/experiments/terrain_stage3b/continuous.gdshader")
const ASSETS := "res://assets/experiments/terrain_c1/"
const SEED := 26026
const COORDS := [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(-1, 0), Vector2i(0, 0)]
const VIEWS := [Vector2(-1100, 750), Vector2(-384, -192), Vector2(0, -1700)]
var _fixture: Dictionary
var _overlays: Array[Dictionary] = []
var _protected: PackedVector2Array
var _anchors: PackedVector2Array
var _earth: Texture2D
var _green: Texture2D
var _metadata: Dictionary[Vector2i, Dictionary] = {}
var _surfaces: Array[Polygon2D] = []
var _next := 0
var _diagnostic := 0
var _failure := ""
var _ready_for_view := false


func _ready() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "fixture.json"))
	if not parsed is Dictionary:
		_fail("Missing C1 fixture")
		return
	_fixture = parsed
	if _fixture.get("seed") != SEED or _fixture.get("rule") != "c1_fields_v1" \
			or _fixture.get("art") != "c1_materials_v1" or _fixture.get("regions", []).size() != 4:
		_fail("Unsupported fixture identity")
		return
	for entry: Dictionary in _fixture.overlays:
		_overlays.append({"polygon": _polygon(entry.polygon), "feather": float(entry.feather),
			"color": Color(float(entry.color[0]), float(entry.color[1]), float(entry.color[2]), float(entry.color[3]))})
	_protected = _polygon(_fixture.gameplay)
	_anchors = _polygon(_fixture.anchors)
	_earth = load(ASSETS + "sources/earth.png") as Texture2D
	_green = load(ASSETS + "sources/green.png") as Texture2D
	if _earth == null or _green == null or _earth.get_size() != Vector2(1254, 1254) \
			or _green.get_size() != Vector2(1254, 1254):
		_fail("Missing/malformed frozen artwork")
		return
	_update_status()
	_clamp_camera()


func _polygon(values: Array) -> PackedVector2Array:
	var points := PackedVector2Array()
	for pair: Array in values:
		points.append(Vector2(float(pair[0]), float(pair[1])))
	return points


func _prepare_chunk(coordinate: Vector2i) -> void:
	if coordinate not in COORDS or _metadata.has(coordinate):
		_fail("Unsupported/duplicate lab chunk")
		return
	var prepared := Metadata.prepare(SEED, coordinate, _overlays, _protected, _anchors)
	if not prepared.get("ok", false):
		_fail("Metadata rejected: " + str(prepared))
		return
	var ids: PackedByteArray = prepared.materials
	if prepared.get("schema") != 1 or prepared.get("seed") != SEED \
			or prepared.get("chunk") != coordinate or ids.size() != 34 * 34:
		_fail("Malformed metadata identity/layout")
		return
	for id in ids:
		if id > 4:
			_fail("Invalid material ID")
			return
	var stem := "%d_%d" % [coordinate.x, coordinate.y]
	var field := load(ASSETS + "fields/" + stem + "_field.png") as Texture2D
	var phase := load(ASSETS + "fields/" + stem + "_phase.png") as Texture2D
	if field == null or phase == null or field.get_size() != Vector2(137, 137) \
			or phase.get_size() != Vector2(7, 7):
		_fail("Missing/malformed C1 shading/phase field")
		return
	var image := Image.create_from_data(34, 34, false, Image.FORMAT_R8, ids)
	if image == null or image.is_empty() or image.has_mipmaps():
		_fail("Invalid numerical image")
		return
	var shader_material := ShaderMaterial.new()
	shader_material.shader = LAB_SHADER
	shader_material.set_shader_parameter("material_ids", ImageTexture.create_from_image(image))
	shader_material.set_shader_parameter("earth_art", _earth)
	shader_material.set_shader_parameter("green_art", _green)
	shader_material.set_shader_parameter("c1_field", field)
	shader_material.set_shader_parameter("phase_field", phase)
	var surface := Polygon2D.new()
	surface.position = Vector2(coordinate) * 2048.0
	surface.polygon = PackedVector2Array([Vector2.ZERO, Vector2(2048, 0), Vector2(2048, 2048), Vector2(0, 2048)])
	surface.material = shader_material
	surface.visible = false
	add_child(surface)
	_surfaces.append(surface)
	_metadata[coordinate] = prepared # Original IDs 1..4 remain available on CPU.


func _process(_delta: float) -> void:
	if not _failure.is_empty() or _fixture.is_empty() or _ready_for_view:
		return
	if _next < COORDS.size():
		_prepare_chunk(COORDS[_next]) # At most one fixed 34x34 preparation per frame.
		_next += 1
	if _failure.is_empty() and _metadata.size() == COORDS.size():
		_ready_for_view = true
		for surface in _surfaces:
			surface.show()
		$CanvasLayer/Curtain.hide()
	_update_status()
	_clamp_camera()


func _clamp_camera() -> void:
	var half_view: Vector2 = get_viewport_rect().size / ($Camera2D.zoom * 2.0)
	half_view = half_view.min(Vector2.ONE * 2048.0)
	$Camera2D.position = $Camera2D.position.clamp(Vector2.ONE * -2048.0 + half_view,
		Vector2.ONE * 2048.0 - half_view)


func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo or not _ready_for_view:
		return
	match key.physical_keycode:
		KEY_1, KEY_2, KEY_3:
			$Camera2D.position = VIEWS[key.physical_keycode - KEY_1]
		KEY_4:
			$Camera2D.zoom = Vector2.ONE
		KEY_5:
			$Camera2D.zoom = Vector2.ONE * 0.5
		KEY_6:
			$Camera2D.zoom = Vector2.ONE * 1.5
		KEY_F:
			_diagnostic = (_diagnostic + 1) % 3
			for surface in _surfaces:
				(surface.material as ShaderMaterial).set_shader_parameter("diagnostic", _diagnostic)
		KEY_ESCAPE:
			get_tree().quit()
	_clamp_camera()
	_update_status()


func _update_status() -> void:
	$CanvasLayer/Status.text = "STAGE 3B LAB / seed %d / chunks %d/4 / ready %s / diagnostic %d\n1 natural | 2 crash area | 3 negative seam | 4/5/6 zoom 1/0.5/1.5 | F art/coverage/IDs | Esc exit\nLive original IDs + Candidate A; NO continuous crash mask. Neutral production tint.\nC1 macro/detail only; no state edits, production overlays, objects or gameplay. %s" % [
		SEED, _metadata.size(), str(_ready_for_view), _diagnostic, _failure]


func _fail(message: String) -> void:
	_failure = message
	_ready_for_view = false
	for surface in _surfaces:
		surface.hide()
	$CanvasLayer/Curtain.show()
	_update_status()
	set_process(false)
	push_error("Stage 3B stopped: " + message)
