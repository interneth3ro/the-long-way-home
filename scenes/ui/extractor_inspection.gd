extends VBoxContainer

signal collect_requested
signal close_requested

const PRODUCING := Color(0.282, 0.663, 0.682)
const BLOCKED := Color(0.773, 0.545, 0.322)
const INACTIVE := Color(0.53, 0.59, 0.60)

@onready var _gauge = $Columns/Production/GaugeCenter/Gauge
@onready var _status: Label = $Columns/Production/Status
@onready var _material: Label = $Columns/Storage/Output/Rows/Material
@onready var _quantity: Label = $Columns/Storage/Output/Rows/Quantity
@onready var _capacity: ProgressBar = $Columns/Storage/Output/Rows/Capacity
@onready var _collect: Button = $Columns/Storage/Collect
@onready var _details: Label = $Columns/Production/DetailsScroll/Details
var _compact: bool = false


func _ready() -> void:
	$Header/Close.pressed.connect(func() -> void: close_requested.emit())
	_collect.pressed.connect(func() -> void: collect_requested.emit())


func set_compact(compact: bool) -> void:
	if compact == _compact:
		return
	_compact = compact
	add_theme_constant_override("separation", 10 if compact else 16)
	$Columns.add_theme_constant_override("separation", 12 if compact else 20)
	_gauge.custom_minimum_size = Vector2.ONE * (144.0 if compact else 164.0)


func refresh(machine: Dictionary, status: PlanetWorldState.OperatingStatus, in_range: bool) -> void:
	var definition: MachineDefinition = machine.definition
	$Header/Title.text = definition.display_name
	var accent := INACTIVE
	_status.text = "Inactive"
	if status == PlanetWorldState.OperatingStatus.PRODUCING:
		_status.text = "Producing"
		accent = PRODUCING
	elif status == PlanetWorldState.OperatingStatus.OUTPUT_FULL:
		_status.text = "Output Full"
		accent = BLOCKED
	_status.add_theme_color_override("font_color", accent)
	var configured := definition.has_production()
	var fraction := float(machine.cycle_progress) / definition.cycle_seconds if configured else 0.0
	_gauge.set_progress(fraction, accent)
	var product := definition.output_item
	_material.text = product.display_name if product != null else "No production configured."
	_quantity.text = "%d / %d" % [machine.output, definition.output_capacity]
	_capacity.value = 100.0 * machine.output / definition.output_capacity if definition.output_capacity > 0 else 0.0
	_collect.disabled = not configured or machine.output <= 0 or not in_range
	_collect.tooltip_text = "Move closer to interact" if not in_range else "Collect all stored output"
	if configured:
		var rate := 60.0 * definition.output_per_cycle / definition.cycle_seconds
		_details.text = "NOMINAL RATE\n%.1f ore/min\nCYCLE DURATION\n%.1f s\nCYCLE YIELD\n%d %s" % [
			rate, definition.cycle_seconds, definition.output_per_cycle, product.display_name]
	else:
		_details.text = "No production configured."
