extends SceneTree
## PR #200 approved only world_coordinates/four checks. The launcher gate is active.
## This two-group manifest is proposed only: DO NOT RUN without separate approval.
## Releasing a group does not isolate globals, autoloads or filesystem changes.

const GROUPS := [
	{"name": "world_coordinates", "script": preload("res://tests/behavioral/smoke_test.gd")},
	{"name": "resource_generation_v2", "script": preload("res://tests/behavioral/resource_generation_v2_test.gd")},
]


func _initialize() -> void:
	var checks: int = 0
	var completed: int = 0
	for entry in GROUPS:
		# The dispatcher owns a fresh RefCounted group; run() is synchronous.
		var group: RefCounted = entry.script.new()
		var result: Variant = group.call("run")
		group = null
		if not result is Dictionary:
			_fail(entry.name, ["run() must return a Dictionary"], completed, checks)
			return
		if not result.get("checks") is int or result.checks <= 0 \
				or not result.get("failures") is Array:
			_fail(entry.name, ["result requires positive int checks and an Array of failure messages"], completed, checks)
			return
		checks += result.checks
		if not result.failures.is_empty():
			_fail(entry.name, result.failures, completed, checks)
			return
		completed += 1
		print("TLWH_BEHAVIORAL_GROUP_V1 %s PASS checks=%d" % [entry.name, result.checks])
	if completed == 0:
		_fail("manifest", ["suite must contain a test group"], completed, checks)
		return
	print("TLWH_BEHAVIORAL_V1 PASS groups=%d checks=%d failures=0" % [completed, checks])
	quit(0)


func _fail(group_name: String, failures: Array, completed: int, checks: int) -> void:
	print("TLWH_BEHAVIORAL_GROUP_V1 %s FAIL" % group_name)
	for failure in failures:
		printerr("%s: %s" % [group_name, str(failure)])
	print("TLWH_BEHAVIORAL_V1 FAIL groups=%d checks=%d failures=%d" % [completed, checks, failures.size()])
	quit(1)
