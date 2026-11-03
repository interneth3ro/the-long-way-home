"""Arrival completion policy and source contracts; never runs Godot/GDScript.

These small independent decision tables specify input/signal authorization.
Source-order checks connect them to the real await/rollback paths; neither is
runtime proof of signals, tween scheduling, physics, or scene-tree pause.
"""
from dataclasses import dataclass, replace
import unittest

from static_automatic_transitions_test import ROOT, function

C = (ROOT/'scenes/main/scene_transition_controller.gd').read_text()
E = (ROOT/'scenes/world/planet_exterior.gd').read_text()


@dataclass(frozen=True)
class Arrival:
    generation: int = 1
    ferrite_token: int = 1
    state: int = 1
    player: int = 1
    seed: int = 26026
    revision: int = 0
    attached: bool = True
    preparing: bool = False
    cancelled: bool = False
    failure: bool = False
    terrain_pending: bool = False
    ferrite_ready: bool = True
    context_matches: bool = True
    centered: bool = True

    def receipt(self):
        return {name:getattr(self,name) for name in
                ('generation','ferrite_token','state','player','seed','revision')} | {'ok':True}

    def ready(self, receipt):
        return (isinstance(receipt,dict) and receipt.get('ok') is True
                and all(receipt.get(k) == v for k,v in self.receipt().items())
                and self.attached and not self.preparing and not self.cancelled
                and not self.failure and not self.terrain_pending and self.ferrite_ready
                and self.context_matches and self.centered)


def decision(destination_ready, *, quick=False, cancel=False, owns=True,
             failure=False, rollback_ready=False):
    if not owns:
        return 'ignore', False, False
    if failure:
        return 'block', False, False
    if quick and cancel:
        return ('source',True,False) if rollback_ready else ('block',False,False)
    return ('destination',True,True) if destination_ready else ('block',False,False)


class TransitionSafetyStaticTest(unittest.TestCase):
    def test_completion_requires_every_required_component(self):
        arrival = Arrival()
        receipt = arrival.receipt()
        self.assertTrue(arrival.ready(receipt))
        for field, value in (('preparing',True),('cancelled',True),('failure',True),
                             ('terrain_pending',True),('ferrite_ready',False),
                             ('context_matches',False),('centered',False),('attached',False)):
            self.assertFalse(replace(arrival,**{field:value}).ready(receipt),field)
        for bad in (None,True,False,{},'ready',{'ok':False,'cancelled':True}):
            self.assertFalse(arrival.ready(bad))
        ready = function(E,'arrival_is_ready')
        for contract in ('result is Dictionary','result.get("ok", false)',
                         '_terrain_failure.is_empty()','_pending.is_empty()',
                         'matches_context(_state)','required_ready(_ferrite_token)',
                         'not _preparing','not _arrival_cancelled','is_ancestor_of(_player)',
                         'WorldCoordinates.world_to_chunk'):
            self.assertIn(contract,ready)

    def test_receipts_are_bound_to_generation_world_seed_revision_player_and_request(self):
        a = Arrival()
        for field in ('generation','ferrite_token','state','player','seed','revision'):
            self.assertFalse(replace(a,**{field:getattr(a,field)+1}).ready(a.receipt()),field)
            self.assertIn(f'result.get("{field}"',function(E,'arrival_is_ready'))

    def test_old_preparation_cannot_clear_new_preparation_flags(self):
        arrival = function(E,'prepare_for_arrival')
        guard = arrival.index('if arrival != _arrival_generation:')
        flag = arrival.index('_preparing = false')
        self.assertLess(guard,flag)
        self.assertIn('return {"ok": false, "cancelled": true}',arrival[guard:flag])
        for method in ('cancel_arrival_preparation','_exit_tree'):
            self.assertIn('_arrival_generation += 1',function(E,method))
        self.assertIn('if not _service_ferrite(true):\n\t\t\tbreak',arrival)
        self.assertIn('return not presented.get("stale", false)',function(E,'_service_ferrite'))

    def test_pause_is_not_a_success_or_failure_guard(self):
        # Whether a paused await happens to resume cannot change authorization.
        for quick in (False,True):
            for paused in (False,True):
                with self.subTest(quick=quick,paused=paused):
                    self.assertEqual(decision(False,quick=quick),('block',False,False))
                    self.assertEqual(decision(False,quick=quick,failure=True),('block',False,False))
        validate = function(C,'_validate_arrival')
        self.assertIn('world.arrival_is_ready(arrival_result)',validate)
        self.assertIn('player.process_mode = Node.PROCESS_MODE_DISABLED',validate)
        self.assertIn('_curtain.color.a = 1.0',validate)
        self.assertIn('get_tree().paused = true',validate)
        self.assertNotIn('_finish_transition(',validate)
        self.assertNotIn('.emit(',validate)

    def test_ordinary_arrival_physics_and_reveal_awaits_revalidate_before_success(self):
        ordinary = function(C,'_perform_transition')
        for wait in ('arrival_result = await destination.call("prepare_for_arrival", player, progression.planet)',
                     'await get_tree().physics_frame'):
            tail = ordinary[ordinary.index(wait)+len(wait):]
            self.assertTrue(tail.lstrip().startswith('if not _validate_arrival(transition, destination, arrival_result):'))
        reveal = ordinary[ordinary.rindex('await _fade_to(0.0)'):]
        self.assertLess(reveal.index('_validate_arrival('),reveal.index('progression.first_exterior_reveal_completed = true'))
        self.assertLess(reveal.index('_validate_arrival('),reveal.index('_finish_transition('))
        self.assertLess(reveal.index('_finish_transition('),reveal.index('transition_completed.emit('))
        self.assertEqual(decision(True),('destination',True,True))

    def test_cancellation_before_or_during_arrival_recovers_only_ready_source(self):
        for phase in ('before_attach','during_arrival','physics_wait'):
            for source_ready in (False,True):
                result=decision(False,quick=True,cancel=True,rollback_ready=source_ready)
                self.assertEqual(result,('source',True,False) if source_ready else ('block',False,False),phase)
        cancel = function(C,'cancel_quick_transition')
        self.assertIn('_arrival_world.call("cancel_arrival_preparation")',cancel)
        quick = function(C,'_perform_quick_transition')
        self.assertIn('await _finish_quick_transition(transition, source)',quick)
        rollback = quick[quick.index('world_host.add_child(source)'):]
        for wait in ('arrival_result = await source.call("prepare_for_arrival", player, progression.planet)',
                     'await get_tree().physics_frame'):
            tail=rollback[rollback.index(wait)+len(wait):]
            self.assertTrue(tail.lstrip().startswith('if not _validate_arrival(transition, source, arrival_result):'))

    def test_real_failure_is_not_disguised_as_recoverable_cancellation(self):
        self.assertEqual(decision(False,quick=True,cancel=True,failure=True,rollback_ready=True),
                         ('block',False,False))
        quick=function(C,'_perform_quick_transition')
        failure=quick.index('not destination.terrain_failure().is_empty()')
        self.assertLess(failure,quick.index('world_host.add_child(source)'))
        self.assertIn('_validate_arrival(transition, destination, arrival_result)\n\t\treturn',quick[failure:])

    def test_finish_fade_rechecks_before_unlock_and_cancelled_travel_has_no_success(self):
        finish=function(C,'_finish_quick_transition')
        fade=finish.index('await _fade_to(0.0')
        self.assertLess(finish.index('_validate_arrival('),fade)
        self.assertLess(fade,finish.rindex('_validate_arrival('))
        self.assertLess(finish.rindex('_validate_arrival('),finish.index('_finish_transition('))
        quick=function(C,'_perform_quick_transition')
        self.assertIn('if not await _finish_quick_transition(',quick)
        self.assertIn('if not _quick_cancelled:\n\t\ttransition_completed.emit',quick)
        self.assertNotIn('first_exterior_reveal_completed',quick)

    def test_controller_detach_new_request_and_reattach_reject_old_callbacks(self):
        for phase in ('fade_out','arrival','physics','rollback','fade_in'):
            self.assertEqual(decision(True,owns=False,quick=True,cancel=True,rollback_ready=True),
                             ('ignore',False,False),phase)
        for method in ('request_transition','_exit_tree'):
            self.assertIn('_transition_generation += 1',function(C,method))
        request=function(C,'request_transition')
        self.assertLess(request.index('var transition := _transition_generation'),request.index('transition_started.emit()'))
        self.assertIn('spawn_name, presentation, transition)',request)
        self.assertNotIn('var transition := _transition_generation',function(C,'_perform_transition'))
        owns=function(C,'_owns_transition')
        for contract in ('transition == _transition_generation','_current_world == world',
                         'is_inside_tree()','world.is_inside_tree()','world.is_ancestor_of(player)'):
            self.assertIn(contract,owns)
        validate=function(C,'_validate_arrival')
        self.assertLess(validate.index('_owns_transition('),validate.index('_arrival_world = null'))
        quick=function(C,'_perform_quick_transition')
        start=quick.index('arrival_result = await destination.call(')
        tail=quick[start:]
        self.assertLess(tail.index('_owns_transition('),tail.index('_arrival_world = null'))

    def test_existing_interior_facing_hooks_keep_void_contract(self):
        room=(ROOT/'scenes/world/v2_room_arrival.gd').read_text()
        self.assertIn('func prepare_for_arrival(player: CharacterBody2D, _planet: PlanetWorldState) -> void:',room)
        self.assertIn('if world is PlanetExterior and not world.arrival_is_ready',function(C,'_validate_arrival'))


if __name__ == '__main__':
    unittest.main()
