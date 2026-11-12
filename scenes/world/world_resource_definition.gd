class_name WorldResourceDefinition
extends Resource
## Inert v2 configuration. Inventory items and placement algorithms are separate.

const ANCHOR_CELLS := Vector2i(4, 4)

@export var resource_id: StringName
# Zero deliberately leaves a new definition unconfigured; no tuning is implied.
@export var abundance_weight: float = 0.0
@export var geological_preferences: Dictionary = {}
@export var allowed_environments: Array[StringName] = []
@export var restricted_environments: Array[StringName] = []
@export_file("*.tres", "*.json") var presentation_catalog: String = ""
@export var anchor_cells: Vector2i = ANCHOR_CELLS


# Canonical tokens avoid whitespace, case aliases and identity delimiters.
static func is_token(value: String) -> bool:
	if value.is_empty():
		return false
	for character in value:
		if not "abcdefghijklmnopqrstuvwxyz0123456789_-".contains(character):
			return false
	return true


static func is_catalog_reference(value: String) -> bool:
	if value.is_empty():
		return true
	if not value.begins_with("res://") or value != value.strip_edges() \
			or not value.get_extension() in ["tres", "json"]:
		return false
	var relative := value.trim_prefix("res://")
	for component in relative.split("/"):
		if component in ["", ".", ".."] or component.contains(":") or component.contains("\\"):
			return false
	return true


# Vocabularies are supplied by a future policy, never invented by this model.
# Empty vocabularies permit only empty optional configuration.
func validation_error(supported_geology: Array[StringName] = [],
		supported_environments: Array[StringName] = []) -> String:
	if not is_token(String(resource_id)):
		return "resource_id must be a nonempty lowercase ASCII token [a-z0-9_-]"
	if not is_finite(abundance_weight) or abundance_weight <= 0.0:
		return "abundance_weight must be finite and greater than zero"
	if anchor_cells != ANCHOR_CELLS:
		return "anchor_cells must be exactly 4x4 construction cells"
	if not is_catalog_reference(presentation_catalog):
		return "presentation_catalog must be empty or a canonical res:// .tres/.json reference"
	for key: Variant in geological_preferences:
		if not (key is String or key is StringName) or not is_token(String(key)) \
				or not supported_geology.has(StringName(key)):
			return "geological_preferences contains an unsupported geology key: %s" % str(key)
		var weight: Variant = geological_preferences[key]
		if not (weight is int or weight is float) or not is_finite(float(weight)) or weight <= 0:
			return "geological_preferences[%s] must be a finite positive weight" % str(key)
	for field in ["allowed_environments", "restricted_environments"]:
		var seen: Dictionary = {}
		for environment: StringName in get(field):
			if not is_token(String(environment)) or not supported_environments.has(environment):
				return "%s contains an unsupported environment: %s" % [field, environment]
			if seen.has(environment):
				return "%s contains a duplicate environment: %s" % [field, environment]
			seen[environment] = true
	for environment in allowed_environments:
		if restricted_environments.has(environment):
			return "environment cannot be both allowed and restricted: %s" % environment
	return ""


static func definitions_error(definitions: Array[WorldResourceDefinition],
		supported_geology: Array[StringName] = [],
		supported_environments: Array[StringName] = []) -> String:
	if definitions.is_empty():
		return "definitions must contain at least one resource"
	var seen: Dictionary = {}
	for index in range(definitions.size()):
		var definition := definitions[index]
		if definition == null:
			return "definitions[%d] must not be null" % index
		var error := definition.validation_error(supported_geology, supported_environments)
		if not error.is_empty():
			return "definitions[%d]: %s" % [index, error]
		if seen.has(definition.resource_id):
			return "definitions[%d]: duplicate resource_id %s" % [index, definition.resource_id]
		seen[definition.resource_id] = true
	return ""
