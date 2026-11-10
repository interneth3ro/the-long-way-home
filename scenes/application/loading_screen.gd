class_name LoadingScreen
extends CanvasLayer

# Operation-neutral presentation. Callers own work, readiness and cancellation.
signal return_requested

enum State { WORKING, COMPLETE, FAILED }
var _state: State = State.WORKING
var _completed: int = 0
var _total: int = 1

@onready var _overlay: ColorRect = $Overlay
@onready var _title: Label = $Overlay/Center/Content/Title
@onready var _status: Label = $Overlay/Center/Content/Status
@onready var _detail: Label = $Overlay/Center/Content/Detail
@onready var _bar: ProgressBar = $Overlay/Center/Content/Progress
@onready var _return: Button = $Overlay/Center/Content/Return


func _ready() -> void:
	_return.pressed.connect(func() -> void: return_requested.emit())


func begin_operation(context: String, total: int, status: String) -> void:
	_state = State.WORKING
	_completed = 0
	_total = maxi(total, 1)
	_overlay.modulate.a = 1.0
	_overlay.show()
	_title.text = context
	_status.text = status
	_detail.text = "0 of %d work units ready" % _total
	_bar.max_value = _total
	_bar.value = 0
	_return.hide()


func report_progress(completed: int, status: String, detail: String) -> void:
	if _state != State.WORKING or completed < _completed:
		return
	# Only explicit successful completion can award the final unit.
	_completed = clampi(completed, _completed, _total - 1)
	_bar.value = _completed
	_status.text = status
	_detail.text = detail


func complete_operation(status: String) -> void:
	if _state != State.WORKING:
		return
	_state = State.COMPLETE
	_completed = _total
	_bar.value = _total
	_status.text = status
	_detail.text = "%d of %d work units ready" % [_total, _total]


func fail_operation(message: String) -> void:
	if _state != State.WORKING:
		return
	_state = State.FAILED
	_overlay.modulate.a = 1.0
	_status.text = "Operation interrupted"
	_detail.text = message
	_return.show()
	_return.grab_focus()


func disable_return() -> void:
	_return.disabled = true
	_return.release_focus()


func fade_out() -> void:
	if _state != State.WORKING:
		return
	var tween := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_overlay, "modulate:a", 0.0, 0.65)
	await tween.finished
