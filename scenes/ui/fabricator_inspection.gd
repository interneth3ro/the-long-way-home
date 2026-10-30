extends VBoxContainer

signal transfer_requested
signal collect_requested
signal change_requested
signal close_requested

# Exact deployed MachineVisual colors; no independent production timer.
const PRODUCING := Color(0.35, 0.78, 0.46)
const OUTPUT_FULL := Color(0.94, 0.69, 0.28)
const INPUT_EMPTY := Color(0.35, 0.60, 0.90)
const INACTIVE := Color(0.55, 0.58, 0.59)

@onready var _gauge = $Columns/Production/GaugeCenter/Gauge
@onready var _status: Label = $Columns/Production/Status
@onready var _ingredients: VBoxContainer = $Columns/Storage/StorageActions/Input/Rows/IngredientsScroll/Ingredients
@onready var _output_material: Label = $Columns/Storage/StorageActions/Output/Rows/Stock/Material
@onready var _output_quantity: Label = $Columns/Storage/StorageActions/Output/Rows/Stock/Quantity
@onready var _output_capacity: ProgressBar = $Columns/Storage/StorageActions/Output/Rows/Capacity
@onready var _notice: Label = $Columns/Storage/StorageActions/Output/Rows/PreviousOutput
@onready var _transfer: Button = $Columns/Storage/StorageActions/Transfer
@onready var _collect: Button = $Columns/Storage/StorageActions/Collect
@onready var _change: Button = $Columns/Production/Change
@onready var _recipe_name: Label = $Columns/Production/Recipe/Rows/Identity/Name
@onready var _recipe_icon: TextureRect = $Columns/Production/Recipe/Rows/Identity/Icon
@onready var _summary: Label = $Columns/Production/Recipe/Rows/Summary
@onready var _rate: Label = $Columns/Production/DetailsScroll/Details/Rows/Rate/Value
@onready var _duration: Label = $Columns/Production/DetailsScroll/Details/Rows/Duration/Value
@onready var _yield: Label = $Columns/Production/DetailsScroll/Details/Rows/Yield/Value
var _compact_mode: int = -1
var _displayed_recipe: RecipeDefinition
var _ingredient_rows: Array[Dictionary] = []


func _ready() -> void:
	$Header/Row/Close.pressed.connect(func() -> void: close_requested.emit())
	_transfer.pressed.connect(func() -> void: transfer_requested.emit())
	_collect.pressed.connect(func() -> void: collect_requested.emit())
	_change.pressed.connect(func() -> void: change_requested.emit())


func mount_chooser(cards: VBoxContainer, pause: Label, error: Label, back: Button) -> void:
	# Move existing controls once; MachineUI retains callbacks, errors and pause ownership.
	cards.reparent($Columns/Chooser/CardsScroll, false)
	cards.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pause.reparent($Columns/Chooser/FeedbackScroll/Feedback, false)
	error.reparent($Columns/Chooser/FeedbackScroll/Feedback, false)
	back.reparent($Columns/Chooser, false)
	back.theme = _change.theme
	back.theme_type_variation = &"B1MachinePrimary"
	back.custom_minimum_size.y = 46


func set_compact(compact: bool) -> void:
	if _compact_mode == int(compact):
		return
	_compact_mode = int(compact)
	add_theme_constant_override("separation", 10 if compact else 16)
	$Columns.add_theme_constant_override("separation", 12 if compact else 20)
	$Columns/Production.add_theme_constant_override("separation", 4 if compact else 6)
	$Columns/Storage.add_theme_constant_override("separation", 6 if compact else 10)
	$Columns/Storage/StorageActions.add_theme_constant_override("separation", 6 if compact else 8)
	$Columns/Production/Heading.visible = not compact
	_gauge.custom_minimum_size = Vector2.ONE * (64.0 if compact else 112.0)
	_recipe_icon.custom_minimum_size = Vector2.ONE * (24.0 if compact else 32.0)
	_summary.add_theme_font_size_override("font_size", 14 if compact else 16)
	_status.add_theme_font_size_override("font_size", 18 if compact else 22)
	$Columns/Production/DetailsScroll.custom_minimum_size.y = 48
	var card := $Columns/Production/Recipe.get_theme_stylebox("panel").duplicate() as StyleBoxFlat
	card.content_margin_top = 6 if compact else 10
	card.content_margin_bottom = 6 if compact else 10
	$Columns/Production/Recipe.add_theme_stylebox_override("panel", card)


func refresh(machine: Dictionary, status: PlanetWorldState.OperatingStatus,
		in_range: bool, product: ItemDefinition, can_transfer: bool, changing: bool) -> void:
	var definition: MachineDefinition = machine.definition
	var recipe := definition.get_recipe(machine.get("recipe_id", &""))
	var choosing := changing or recipe == null
	$Header/Row/Title.text = definition.display_name.to_upper()
	$Columns/Storage/StorageActions.visible = not choosing
	$Columns/Production.visible = not choosing
	$Columns/Chooser.visible = choosing
	$Columns/Chooser/Heading.text = "CHANGE RECIPE" if changing else "SELECT RECIPE"
	$Columns/Chooser/FeedbackScroll.visible = changing
	if choosing:
		return
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
	_gauge.set_progress(float(machine.cycle_progress) / recipe.cycle_seconds, accent)
	if _displayed_recipe != recipe:
		_build_ingredients(recipe)
	for row in _ingredient_rows:
		var stored: int = machine.inputs.get(row.item_id, 0)
		row.quantity.text = "%d / %d" % [stored, definition.input_capacity]
		row.bar.value = 100.0 * stored / definition.input_capacity if definition.input_capacity > 0 else 0.0
	# Nonempty output always uses its independently stored identity.
	_output_material.text = product.display_name if machine.output > 0 and product != null else "No stored output"
	_output_quantity.text = "%d / %d" % [machine.output, definition.output_capacity]
	_output_capacity.value = 100.0 * machine.output / definition.output_capacity if definition.output_capacity > 0 else 0.0
	_notice.visible = machine.output > 0 and product != null and product.item_id != recipe.output_item.item_id
	_transfer.disabled = not can_transfer or not in_range
	_collect.disabled = machine.output <= 0 or product == null or not in_range
	_change.disabled = not in_range
	_transfer.tooltip_text = "Transfer all eligible inputs up to each capacity" if in_range else "Move closer to interact"
	_collect.tooltip_text = "Collect all stored output" if in_range else "Move closer to interact"
	_change.tooltip_text = "Change the selected recipe" if in_range else "Move closer to interact"
	_recipe_name.text = recipe.display_name
	_recipe_icon.texture = recipe.icon
	_recipe_icon.visible = recipe.icon != null
	_summary.text = "%s → %s" % [recipe.input_summary(), recipe.output_summary()]
	_rate.text = "%.1f items/min" % (60.0 * recipe.output_quantity / recipe.cycle_seconds)
	_duration.text = "%.1f s" % recipe.cycle_seconds
	_yield.text = recipe.output_summary()


func _build_ingredients(recipe: RecipeDefinition) -> void:
	_displayed_recipe = recipe
	for child in _ingredients.get_children():
		_ingredients.remove_child(child)
		child.queue_free()
	_ingredient_rows.clear()
	for ingredient in recipe.ingredients:
		var row := VBoxContainer.new()
		var stock := HBoxContainer.new()
		var material := Label.new()
		material.text = ingredient.item.display_name
		material.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		material.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var quantity := Label.new()
		stock.add_child(material)
		stock.add_child(quantity)
		var bar := ProgressBar.new()
		bar.custom_minimum_size.y = 7
		bar.show_percentage = false
		bar.step = 0.1
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(stock)
		row.add_child(bar)
		_ingredients.add_child(row)
		_ingredient_rows.append({"item_id": ingredient.item.item_id, "quantity": quantity, "bar": bar})
