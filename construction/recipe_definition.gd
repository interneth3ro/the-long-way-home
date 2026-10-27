class_name RecipeDefinition
extends Resource

@export var recipe_id: StringName
@export var display_name: String
@export var ingredients: Array[RecipeIngredient] = []
@export var output_item: ItemDefinition
@export var output_quantity: int = 1
@export var cycle_seconds: float = 3.0
@export var icon: Texture2D


func is_valid() -> bool:
	if recipe_id == &"" or display_name.strip_edges().is_empty() or ingredients.is_empty() \
			or output_item == null or not output_item.is_valid() or output_quantity <= 0 \
			or not is_finite(cycle_seconds) or cycle_seconds <= 0.0:
		return false
	var seen: Dictionary = {}
	for ingredient in ingredients:
		if ingredient == null or not ingredient.is_valid() or seen.has(ingredient.item.item_id):
			return false
		seen[ingredient.item.item_id] = true
	return true


func input_summary() -> String:
	var parts := PackedStringArray()
	for ingredient in ingredients:
		parts.append("%d %s" % [ingredient.quantity, ingredient.item.display_name])
	return " + ".join(parts)


func output_summary() -> String:
	return "%d %s%s" % [output_quantity, output_item.display_name,
		"s" if output_quantity != 1 else ""]
