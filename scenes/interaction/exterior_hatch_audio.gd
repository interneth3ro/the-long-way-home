class_name ExteriorHatchAudio
extends AudioStreamPlayer

# One local voice; no simulation, collision or travel ownership.
const OPEN_SOUND: AudioStream = preload("res://assets/audio/exterior_hatch/hatch_open.wav")
const CLOSE_SOUND: AudioStream = preload("res://assets/audio/exterior_hatch/hatch_close.wav")
const RAMP_SECONDS: float = 0.012
const PLAY_VOLUME: float = 0.65

var _direction: int = 0
var _openness: float = 0.0
var _switching: bool = false
var _ramp: Tween


func _ready() -> void:
	var transitions := get_tree().get_first_node_in_group(&"scene_transitions") as SceneTransitionController
	if transitions != null:
		transitions.transition_started.connect(_silence)


func update_motion(opening: bool, current_openness: float) -> void:
	_openness = current_openness
	var direction := 1 if opening else -1
	if direction == _direction:
		return
	_direction = direction
	# A reversal during the short fade only changes the pending direction.
	if _switching:
		return
	if _ramp != null:
		_ramp.kill()
	if playing:
		_switching = true
		_ramp = create_tween()
		_ramp.tween_property(self, "volume_linear", 0.0, RAMP_SECONDS)
		_ramp.tween_callback(_play_direction)
	else:
		_play_direction()


func _play_direction() -> void:
	stop()
	_switching = false
	stream = OPEN_SOUND if _direction > 0 else CLOSE_SOUND
	# Skip already-travelled motion on reversal, retaining the endpoint latch.
	var fraction := _openness if _direction > 0 else 1.0 - _openness
	volume_linear = 0.0
	play(clampf(fraction, 0.0, 1.0) * stream.get_length())
	_ramp = create_tween()
	_ramp.tween_property(self, "volume_linear", PLAY_VOLUME, RAMP_SECONDS)


func _silence() -> void:
	# The controller also emits while this exterior is detached in its cache.
	if not is_inside_tree():
		return
	if _ramp != null:
		_ramp.kill()
	_direction = 0
	_switching = false
	_ramp = create_tween()
	_ramp.tween_property(self, "volume_linear", 0.0, RAMP_SECONDS)
	_ramp.tween_callback(stop)


func reset_audio() -> void:
	if _ramp != null:
		_ramp.kill()
	stop()
	_direction = 0
	_switching = false
	volume_linear = 0.0


func _exit_tree() -> void:
	# Cached worlds are detached, not freed. Kill callbacks and playback on both.
	reset_audio()
