extends VBoxContainer

signal transfer_requested
signal collect_requested
signal close_requested

# Match the deployed MachineVisual status dot; it has no cycle-progress display.
const PRODUCING := Color(0.35, 0.78, 0.46)
const OUTPUT_FULL := Color(0.94, 0.69, 0.28)
const INPUT_EMPTY := Color(0.35, 0.60, 0.90)
const INACTIVE := Color(0.55, 0.58, 0.59)

@onready var _gauge = $Columns/Production/GaugeCenter/Gauge
@onready var _status: Label = $Columns/Production/Status
@onready var _input_material: Label = $Columns/Storage/StorageActions/Input/Rows/Stock/Material
@onready var _input_quantity: Label = $Columns/Storage/StorageActions/Input/Rows/Stock/Quantity
@onready var _input_capacity: ProgressBar = $Columns/Storage/StorageActions/Input/Rows/Capacity
@onready var _output_material: Label = $Columns/Storage/StorageActions/Output/Rows/Stock/Material
@onready var _output_quantity: Label = $Columns/Storage/StorageActions/Output/Rows/Stock/Quantity
@onready var _output_capacity: ProgressBar = $Columns/Storage/StorageActions/Output/Rows/Capacity
@onready var _transfer: Button = $Columns/Storage/StorageActions/Transfer
@onready var _collect: Button = $Columns/Storage/StorageActions/Collect
@onready var _details: VBoxContainer = $Columns/Production/DetailsScroll/Details/Rows
@onready var _recipe: Label = $Columns/Production/DetailsScroll/Details/Rows/Recipe/Value
@onready var _rate: Label = $Columns/Production/DetailsScroll/Details/Rows/Rate/Value
@onready var _duration: Label = $Columns/Production/DetailsScroll/Details/Rows/Duration/Value
@onready var _yield: Label = $Columns/Production/DetailsScroll/Details/Rows/Yield/Value
@onready var _unavailable: Label = $Columns/Production/DetailsScroll/Details/Unavailable
var _compact: bool = false
var _input_icon: TextureRect
var _output_icon: TextureRect


func _ready() -> void:
	_input_icon = ItemPresentation.add_material_icon(_input_material)
	_output_icon = ItemPresentation.add_material_icon(_output_material)
	$Header/Row/Close.pressed.connect(func() -> void: close_requested.emit())
	_transfer.pressed.connect(func() -> void: transfer_requested.emit())
	_collect.pressed.connect(func() -> void: collect_requested.emit())


func set_compact(compact: bool) -> void:
	if compact == _compact:
		return
	_compact = compact
	add_theme_constant_override("separation", 10 if compact else 16)
	$Columns.add_theme_constant_override("separation", 12 if compact else 20)
	_gauge.custom_minimum_size = Vector2.ONE * (124.0 if compact else 144.0)


func refresh(machine: Dictionary, status: PlanetWorldState.OperatingStatus,
		in_range: bool, available_input: int) -> void:
	var definition: MachineDefinition = machine.definition
	$Header/Row/Title.text = definition.display_name.to_upper()
	var accent := INACTIVE
	_status.text = "Inactive"
	match status:
		PlanetWorldState.OperatingStatus.PRODUCING:
			_status.text = "Producing"
			accent = PRODUCING
		PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			_status.text = "Output Full"
			accent = OUTPUT_FULL
		PlanetWorldState.OperatingStatus.INPUT_EMPTY:
			_status.text = "Input Empty"
			accent = INPUT_EMPTY
	_status.add_theme_color_override("font_color", accent)
	var configured := definition.has_production() and definition.has_input()
	var fraction := float(machine.cycle_progress) / definition.cycle_seconds if configured else 0.0
	_gauge.set_progress(fraction, accent)
	ItemPresentation.set_material_icon(_input_icon, definition.input_item, machine.input)
	ItemPresentation.set_material_icon(_output_icon, definition.output_item, machine.output)
	_input_material.text = (definition.input_item.display_name if machine.input > 0 else "Input") \
		if definition.has_input() else "No input configured."
	_output_material.text = (definition.output_item.display_name if machine.output > 0 else "Output") \
		if definition.output_item != null else "No output configured."
	_input_quantity.text = "%d / %d" % [machine.input, definition.input_capacity]
	_output_quantity.text = "%d / %d" % [machine.output, definition.output_capacity]
	_input_capacity.value = 100.0 * machine.input / definition.input_capacity \
		if definition.input_capacity > 0 else 0.0
	_output_capacity.value = 100.0 * machine.output / definition.output_capacity \
		if definition.output_capacity > 0 else 0.0
	_transfer.disabled = not configured or machine.input >= definition.input_capacity \
		or available_input <= 0 or not in_range
	_collect.disabled = not configured or machine.output <= 0 or not in_range
	_transfer.tooltip_text = "Move closer to interact" \
		if not in_range else "Transfer all eligible input up to capacity"
	_collect.tooltip_text = "Move closer to interact" if not in_range else "Collect all stored output"
	_details.visible = configured
	_unavailable.visible = not configured
	if configured:
		var ingredient := "%d %s" % [definition.input_per_cycle, definition.input_item.display_name]
		var product := "%d %s" % [definition.output_per_cycle, definition.output_item.display_name]
		var conversion := "%s → %s" % [ingredient, product]
		var font := _recipe.get_theme_font("font")
		var font_size := _recipe.get_theme_font_size("font_size")
		var text_width := font.get_string_size(conversion, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
		# Prefer a complete conversion line; otherwise keep each material phrase
		# together on its own line. Ordinary wrapping remains for narrower windows.
		_recipe.text = conversion if text_width <= _recipe.size.x \
			else "%s\n→ %s" % [ingredient, product]
		var rate := 60.0 * definition.output_per_cycle / definition.cycle_seconds
		_rate.text = "%.1f ingots/min" % rate
		_duration.text = "%.1f s" % definition.cycle_seconds
		_yield.text = "%d %s" % [definition.output_per_cycle, definition.output_item.display_name]
