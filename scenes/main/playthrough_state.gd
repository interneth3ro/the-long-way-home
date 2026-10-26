class_name PlaythroughState
extends Node

# Session state only. A fresh Main instance is a new playthrough.
# No disk save/load workflow exists yet; do not store this in project settings.
var first_exterior_reveal_completed: bool = false
