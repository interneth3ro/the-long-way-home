class_name RecipeIngredient
extends Resource

@export var item: ItemDefinition
@export var quantity: int = 1


func is_valid() -> bool:
	return item != null and item.is_valid() and item.section == ItemDefinition.Section.MATERIALS \
		and quantity > 0
