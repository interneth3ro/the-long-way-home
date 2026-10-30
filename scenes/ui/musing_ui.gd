class_name MusingUI
extends CanvasLayer

const MAX_WIDTH := 360.0
const MAX_HEIGHT := 300.0
const EDGE_CLEARANCE := 24.0
const BOTTOM_CLEARANCE := 112.0

@onready var _panel: PanelContainer = $HUD/Panel
@onready var _text: Label = $HUD/Panel/Content/Scroll/Text
@onready var _scroll: ScrollContainer = $HUD/Panel/Content/Scroll
# Capture before Main reparents Dave into the current environment.
@onready var _dialogue: DialogueUI = get_parent().get_node("Dave/DialogueUI")
@onready var _transitions: SceneTransitionController = get_parent().get_node("SceneTransitions")

var _tween: Tween
var _active: MusingDefinition
var _pending: MusingDefinition
var _reading_fraction: float = 0.0
var _layout_queued: bool = false


func _ready() -> void:
	$HUD.scale_changed.connect(_queue_layout)
	_text.minimum_size_changed.connect(_queue_layout)
	_queue_layout()


func _process(_delta: float) -> void:
	# Resolve priority before drawing, including close/transition in the same
	# frame. No progression callbacks or conversation ownership changes.
	if _transitions.is_transitioning():
		dismiss()
	elif _dialogue.is_conversation_open():
		if _active != null:
			_pending = _active
			_stop_display()
	elif _pending != null:
		var definition := _pending
		_pending = null
		show_musing(definition)
	if _active != null:
		# Future oversized observations scroll passively, holding at both ends.
		var travel := maxf(0.0, _text.size.y - _scroll.size.y)
		_scroll.scroll_vertical = roundi(travel * clampf((_reading_fraction - 0.15) / 0.70, 0.0, 1.0))


func show_musing(definition: MusingDefinition) -> void:
	if definition == null or definition.text.strip_edges().is_empty():
		return
	if _transitions.is_transitioning():
		dismiss()
		return
	if _dialogue.is_conversation_open():
		_stop_display()
		_pending = definition
		return

	dismiss()
	_active = definition
	_text.text = definition.text
	_reading_fraction = 0.0
	_scroll.scroll_vertical = 0
	_queue_layout()
	_panel.modulate.a = 0.0
	_panel.show()
	_tween = create_tween()
	_tween.tween_property(_panel, "modulate:a", 1.0, 0.30).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_method(_set_reading_fraction, 0.0, 1.0, definition.duration_seconds)
	_tween.tween_property(_panel, "modulate:a", 0.0, 0.40).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(dismiss)


func _set_reading_fraction(value: float) -> void:
	_reading_fraction = value


func dismiss() -> void:
	# Main already calls this on transition_started: discard visible AND pending.
	_pending = null
	_stop_display()


func _stop_display() -> void:
	if _tween != null:
		_tween.kill()
		_tween = null
	_active = null
	_panel.hide()
	_text.text = ""


func _queue_layout() -> void:
	if not _layout_queued:
		_layout_queued = true
		_layout_panel.call_deferred()


func _layout_panel() -> void:
	_layout_queued = false
	var extent: Vector2 = $HUD.size
	var style := _panel.get_theme_stylebox("panel")
	var content := $HUD/Panel/Content as VBoxContainer
	var identity := $HUD/Panel/Content/Identity as HBoxContainer
	var chrome: Vector2 = style.get_minimum_size()
	var font := _text.get_theme_font("font")
	var font_size := _text.get_theme_font_size("font_size")
	var natural_width := identity.get_combined_minimum_size().x
	for line: String in _text.text.split("\n"):
		natural_width = maxf(natural_width, font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x)
	_panel.size.x = minf(natural_width + chrome.x, minf(MAX_WIDTH, extent.x - EDGE_CLEARANCE * 2.0))
	var header_height := identity.get_combined_minimum_size().y + content.get_theme_constant("separation")
	var maximum_height := minf(MAX_HEIGHT, extent.y - BOTTOM_CLEARANCE - EDGE_CLEARANCE)
	_scroll.custom_minimum_size.y = minf(_text.get_minimum_size().y,
		maxf(24.0, maximum_height - chrome.y - header_height))
	_panel.size.y = _panel.get_combined_minimum_size().y
	_panel.position = Vector2(EDGE_CLEARANCE, extent.y - BOTTOM_CLEARANCE - _panel.size.y)
