extends CanvasLayer

# Persistent, Computer-specific presentation; no world or production authority.
const CONTENT_PATH := "res://dialogue/computer_restoration.json"
const LEGACY_REPAIRED: Texture2D = preload("res://assets/environment/computer/computer_repaired_pilot.png")
const DIALOGUE_SCENE: PackedScene = preload("res://scenes/ui/dialogue_ui.tscn")
const CHARACTERS_PER_SECOND := 15.0
const MIN_LINE_SECONDS := 2.5
const MAX_LINE_SECONDS := 8.0
const SCENE_GAP_SECONDS := 1.5
const FADE_SECONDS := 0.35

@onready var _main: Node = get_parent()
@onready var _state: PlaythroughState = _main.get_node("PlaythroughState")
@onready var _transitions: SceneTransitionController = _main.get_node("SceneTransitions")
@onready var _player: CharacterBody2D = _transitions.player
@onready var _detector: InteractionDetector = _player.get_node("InteractionDetector")
@onready var _dialogue: DialogueUI = _player.get_node("DialogueUI")
@onready var _interaction: InteractionUI = _player.get_node("InteractionUI")
@onready var _panel: PanelContainer = $HUD/Panel
@onready var _confirm: Button = $HUD/Panel/Content/Restore
@onready var _curtain: ColorRect = $Curtain

var _target: WorldInteractable
var _inspection_pending: bool = false
var _content: Dictionary = {}
var _cinematic: bool = false
var _playback: DialogueUI
var _cues: Array[Dictionary] = []
var _cue_index: int = 0
var _remaining: float = 0.0
var _fading: bool = false
var _tween: Tween
var _flicker: Tween
var _display: Sprite2D
var _previous_player_mode: Node.ProcessMode
var _suspended: Array[Dictionary] = []
var _hum: AudioStreamPlayer


func _ready() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONTENT_PATH))
	if parsed is Dictionary:
		_content = parsed
	_detector.computer_restoration = self
	_dialogue.conversation_completed.connect(_on_conversation_completed)
	_dialogue.conversation_dismissed.connect(_on_conversation_dismissed)
	_state.inventory.changed.connect(_refresh)
	_transitions.transition_started.connect(_on_transition)
	_transitions.transition_completed.connect(_on_arrival)
	$HUD.scale_changed.connect(_layout)
	_panel.minimum_size_changed.connect(_layout, CONNECT_DEFERRED)
	var style := _panel.get_theme_stylebox("panel").duplicate() as StyleBoxFlat
	style.set_border_width_all(0)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	_panel.add_theme_stylebox_override("panel", style)
	_layout.call_deferred()
	_sync_visual.call_deferred()


func handles(target: WorldInteractable) -> bool:
	return target != null and target.conversation != null \
		and target.conversation.conversation_id == &"computer_opening"


func interaction_blocked() -> bool:
	return _panel.visible or _cinematic


func interact_with(target: WorldInteractable) -> void:
	if interaction_blocked() or not handles(target) or not _context_available(target):
		return
	_target = target
	if not _state.computer_opening_completed:
		_dialogue.show_conversation(target.conversation)
	elif _state.computer_restored:
		_dialogue.show_conversation(_conversation("computer_operational", _content.get("operational", [])))
	elif not _state.ferrite_plate_acquired:
		_interaction.show_response(target.inspection_response)
	elif not _state.computer_inspection_completed:
		_inspection_pending = _dialogue.show_conversation(
			_conversation("computer_inspection", _content.get("inspection", [])))
	else:
		_open_panel()
	_interaction.set_prompt("")


func _context_available(target: WorldInteractable) -> bool:
	if not is_instance_valid(target) or not target.is_inside_tree() or not target.can_interact() \
			or _transitions.is_transitioning() or _dialogue.is_conversation_open() \
			or _interaction.is_response_open() \
			or _main.get_node("InventoryUI").is_open() or _main.get_node("MachineUI").is_open() \
			or _main.get_node("Construction").is_active():
		return false
	var world := _transitions.get_current_world()
	if world == null or not world.is_ancestor_of(target):
		return false
	var radius: float = (_detector.get_node("CollisionShape2D").shape as CircleShape2D).radius
	if target.max_interaction_distance > 0.0:
		radius = minf(radius, target.max_interaction_distance)
	return _detector.global_position.distance_to(target.to_global(target.interaction_point)) <= radius


func _conversation(id: String, lines: Array) -> DialogueConversation:
	var conversation := DialogueConversation.new()
	conversation.conversation_id = StringName(id)
	for index in lines.size():
		var line: Dictionary = lines[index]
		conversation.entries.append(_entry(line, id + "." + str(index)))
	return conversation


func _entry(line: Dictionary, id: String) -> DialogueEntry:
	var entry := DialogueEntry.new()
	entry.entry_id = StringName(id)
	entry.speaker_id = StringName(line.get("speaker", ""))
	entry.speaker_display_name = "Dave" if entry.speaker_id == &"dave" else "Computer"
	entry.text = line.get("text", "")
	return entry


func _on_conversation_completed(id: StringName) -> void:
	if id == &"computer_opening":
		_state.computer_opening_completed = true
	elif id == &"computer_inspection" and _inspection_pending:
		_inspection_pending = false
		_state.computer_inspection_completed = true
		_open_panel.call_deferred()


func _on_conversation_dismissed(id: StringName) -> void:
	if id == &"computer_inspection":
		# Dismissal retries the whole exchange on the next interaction.
		_inspection_pending = false


func _open_panel() -> void:
	if _cinematic or _state.computer_restored or not _state.computer_inspection_completed \
			or not _context_available(_target):
		return
	_panel.show()
	_main.get_node("InventoryUI").close()
	_main.get_node("HotbarUI").dismiss_context_menu()
	_refresh()
	_layout()
	$HUD/Panel/Content/NotYet.grab_focus()


func close() -> void:
	_panel.hide()
	_confirm.release_focus()
	$HUD/Panel/Content/NotYet.release_focus()


func _refresh() -> void:
	$HUD/Panel/Content/Plates.text = "Ferrite Plates: %d / 4" % _state.inventory.get_quantity(PlaythroughState.FERRITE_PLATE.item_id)
	$HUD/Panel/Content/Rods.text = "Ferrite Rods: %d / 4" % _state.inventory.get_quantity(PlaythroughState.FERRITE_ROD.item_id)
	_confirm.disabled = not _state.can_restore_computer() or _cinematic


func _layout() -> void:
	_panel.size = Vector2(minf(420.0, $HUD.size.x - 48.0), 0.0)
	_panel.position = ($HUD.size - _panel.size) * 0.5


func _input(event: InputEvent) -> void:
	if _cinematic:
		# No keyboard, mouse, E or Esc advancement. GUI scrolling remains possible
		# for accessibility through the separate playback instance's text region.
		if not event is InputEventMouseButton or event.button_index not in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			get_viewport().set_input_as_handled()
	elif _panel.visible and not event.is_echo() and event.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if _panel.visible and not _context_available(_target):
		close()
	if not _cinematic:
		return
	var world := _transitions.get_current_world()
	if not is_instance_valid(_target) or not _target.is_inside_tree() \
			or world == null or not world.is_ancestor_of(_target):
		_cleanup()
		_sync_visual()
		return
	if _fading:
		return
	_remaining -= delta
	if _remaining <= 0.0:
		_next_cue()


func _confirm_repair() -> void:
	if not _panel.visible or _cinematic or not _context_available(_target) or not _prepare_cues():
		return
	# Claim UI/input ownership before the synchronous material transaction.
	_cinematic = true
	close()
	_lock_presentation()
	if not _state.restore_computer():
		_cleanup()
		return
	# Synchronous observers may tear down the presenter after the committed repair.
	if not is_inside_tree() or not _cinematic:
		return
	_fade_out()


func _prepare_cues() -> bool:
	_cues.clear()
	var scenes: Array = _content.get("scenes", [])
	if scenes.size() != 4:
		return false
	for index in scenes.size():
		if index > 0:
			_cues.append({"kind": "gap"})
		var scene: Dictionary = scenes[index]
		var cues: Array = scene.get("cues", [])
		if cues.is_empty():
			return false
		for value in cues:
			if not value is Dictionary:
				return false
			var cue: Dictionary = value
			if cue.get("kind") == "line":
				if cue.get("speaker") not in ["dave", "computer"] or not _entry(cue, "validation").is_valid():
					return false
			elif cue.get("kind") != "direction" or String(cue.get("text", "")).is_empty():
				return false
			_cues.append(cue)
	return true


func _lock_presentation() -> void:
	_previous_player_mode = _player.process_mode
	_player.velocity = Vector2.ZERO
	_player.call("_update_walk_animation", Vector2.ZERO)
	_detector.clear_for_transition()
	_player.process_mode = Node.PROCESS_MODE_DISABLED
	# Hide and suspend persistent competing presenters, preserving preferences.
	for presenter_name in ["InventoryUI", "MachineUI", "Construction", "HotbarUI", "ObjectiveTracker", "MusingUI", "UIScalePreview"]:
		var node := _main.get_node_or_null(presenter_name)
		if node == null:
			continue
		var canvas := node as CanvasLayer
		_suspended.append({"node": node, "mode": node.process_mode,
			"visible": canvas.visible if canvas != null else true})
		if canvas != null:
			canvas.hide()
		node.process_mode = Node.PROCESS_MODE_DISABLED
	_playback = DIALOGUE_SCENE.instantiate() as DialogueUI
	_playback.layer = layer + 1
	add_child(_playback)
	_cue_index = 0


func _fade_out() -> void:
	_fading = true
	_curtain.show()
	_tween = create_tween()
	_tween.tween_property(_curtain, "color:a", 1.0, FADE_SECONDS)
	_tween.tween_callback(_reveal_repair)


func _reveal_repair() -> void:
	_sync_visual()
	_start_hum()
	_tween = create_tween()
	_tween.tween_property(_curtain, "color:a", 0.0, FADE_SECONDS)
	_tween.tween_callback(_begin_script)


func _begin_script() -> void:
	_curtain.hide()
	_fading = false
	_next_cue()


func _next_cue() -> void:
	if _cue_index >= _cues.size():
		# Activate the next objective while its presenter is still suppressed.
		_state.finish_computer_cinematic()
		_cleanup()
		return
	var cue := _cues[_cue_index]
	_cue_index += 1
	if cue.kind == "line":
		_playback.show_automatic_entry(_entry(cue, "restoration." + str(_cue_index)))
		$HUD/Direction.text = ""
		_remaining = clampf(String(cue.text).length() / CHARACTERS_PER_SECOND, MIN_LINE_SECONDS, MAX_LINE_SECONDS)
	else:
		_playback.close_automatic()
		$HUD/Direction.text = cue.get("text", "")
		_remaining = SCENE_GAP_SECONDS if cue.kind == "gap" else 1.5
		if "flicker" in String(cue.get("text", "")) and is_instance_valid(_display):
			_flicker = create_tween()
			_flicker.tween_property(_display, "modulate:a", 0.55, 0.08)
			_flicker.tween_property(_display, "modulate:a", 1.0, 0.12)


func _sync_visual() -> void:
	var world := _transitions.get_current_world()
	if world == null:
		return
	var damaged := world.get_node_or_null("VisualContent/ComputerDamaged") as Sprite2D
	var repaired := world.get_node_or_null("VisualContent/ComputerRepairedInactive") as Sprite2D
	if damaged != null and repaired != null:
		damaged.visible = not _state.computer_restored
		repaired.visible = _state.computer_restored
		_display = repaired
	else:
		var legacy := world.get_node_or_null("GroundObjects/WestObstacle/Visual/Sprite2D") as Sprite2D
		if legacy != null and _state.computer_restored:
			legacy.texture = LEGACY_REPAIRED
			_display = legacy


func _start_hum() -> void:
	# Quiet, seamless 80 Hz tone; no new source artwork/audio asset or import.
	var samples := PackedByteArray()
	samples.resize(22050)
	for index in 11025:
		var sample := int(sin(TAU * 80.0 * index / 22050.0) * 1600.0)
		samples.encode_s16(index * 2, sample)
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	stream.data = samples
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_end = 11025
	_hum = AudioStreamPlayer.new()
	_hum.stream = stream
	_hum.volume_db = -18.0
	add_child(_hum)
	_hum.play()


func _on_transition() -> void:
	_inspection_pending = false
	close()


func _on_arrival(_source: String, _destination: String) -> void:
	_sync_visual()


func _cleanup() -> void:
	if _tween != null:
		_tween.kill()
	if _flicker != null:
		_flicker.kill()
	if is_instance_valid(_display):
		_display.modulate.a = 1.0
	_curtain.color.a = 0.0
	_curtain.hide()
	$HUD/Direction.text = ""
	if is_instance_valid(_hum):
		_hum.stop()
		_hum.queue_free()
	_hum = null
	if is_instance_valid(_playback):
		_playback.close_automatic()
		_playback.queue_free()
	_playback = null
	if _cinematic and is_instance_valid(_player):
		_player.velocity = Vector2.ZERO
		_player.process_mode = _previous_player_mode
	for record in _suspended:
		var node: Node = record.node
		if is_instance_valid(node):
			node.process_mode = record.mode
			if node is CanvasLayer:
				node.visible = record.visible
	_suspended.clear()
	_cues.clear()
	_remaining = 0.0
	_fading = false
	_cinematic = false


func _exit_tree() -> void:
	if not is_instance_valid(_panel):
		return
	close()
	_cleanup()
	if is_instance_valid(_detector) and _detector.computer_restoration == self:
		_detector.computer_restoration = null
