import json

nb = json.load(open('competition_notebook.ipynb'))
cell9 = nb['cells'][9]
src = ''.join(cell9['source'])

# v60: Replace single-level coord-BFS (Tier 1b) with multi-level per-level re-probe.
# This is the compositional-balance improvement: treat each level as an independent
# problem, re-classify mechanics at the level boundary, select the right solver.

OLD_TIER_1B = (
    '        # --- Tier 1b: coordinate-click BFS (for games where action6 uses x,y data) ---\n'
    '        if 6 in available_actions and (_time.time() - t0) < t_budget * 0.70:\n'
    '            # If all standard probes returned no frame change, this is a coord-click game\n'
    '            all_no_frame = bool(probe) and all(\n'
    '                not v.get(\'frame_changed\') for v in probe.values())\n'
    '            no_probe = not probe\n'
    '            if all_no_frame or no_probe:\n'
    '                if verbose:\n'
    '                    print(f"    [{game_id}] coord-BFS: probing coordinate effects")\n'
    '                sc_coords, ac_coords = _probe_coord_effects(\n'
    '                    game_obj, ActionInput_cls, action_num=6)\n'
    '                coords = sc_coords + ac_coords\n'
    '                if coords:\n'
    '                    coords = _dedup_coords(game_obj, ActionInput_cls, 6, coords)\n'
    '                    n_c = len(coords)\n'
    '                    coord_nodes = min(n_c ** 4 * 2, 200000)\n'
    '                    if verbose:\n'
    '                        print(f"    [{game_id}] coord-BFS: {n_c} unique coords "\n'
    '                              f"budget={coord_nodes}")\n'
    '                    coord_seq = _coordinate_bfs(\n'
    '                        game_obj, ActionInput_cls, 6, coords,\n'
    '                        max_depth=30, max_nodes=coord_nodes,\n'
    '                        verbose=verbose, game_id=game_id,\n'
    '                    )\n'
    '                    if coord_seq:\n'
    '                        try:\n'
    '                            obs2 = env.reset()\n'
    '                            acts = 0\n'
    '                            lc = 0\n'
    '                            for _step in coord_seq:\n'
    '                                _an2 = _step[\'action\']\n'
    '                                _action2 = getattr(\n'
    '                                    GameAction, f\'ACTION{_an2}\', GameAction.ACTION6)\n'
    '                                _data2 = _step.get(\'data\')\n'
    '                                obs2 = env.step(_action2, data=_data2)\n'
    '                                acts += 1\n'
    '                                if obs2 is None:\n'
    '                                    break\n'
    '                                if obs2.state == GameState.WIN:\n'
    '                                    lc = getattr(obs2, \'levels_completed\', lc + 1)\n'
    '                                    sc2 = lc / win_levels if win_levels > 0 else 1.0\n'
    '                                    if verbose:\n'
    '                                        print(f"    [{game_id}] coord-BFS win: "\n'
    '                                              f"score={sc2:.3f} levels={lc}")\n'
    '                                    return sc2, lc, acts, coord_seq\n'
    '                                elif obs2.state == GameState.GAME_OVER:\n'
    '                                    break\n'
    '                        except Exception as _e:\n'
    '                            if verbose:\n'
    '                                print(f"    [{game_id}] coord-BFS exec error: {_e}")\n'
)

NEW_TIER_1B = r"""        # --- Tier 1b: multi-level coord-BFS (v60: per-level re-probe) ---
        # Compositional approach: re-classify each level independently (blackboard pattern).
        # At each level boundary, re-probe to detect coord-click vs action-based mechanics.
        if 6 in available_actions and (_time.time() - t0) < t_budget * 0.70:
            # Trigger if initial probe showed no frame changes (coord-click game)
            all_no_frame = bool(probe) and all(
                not v.get('frame_changed') for v in probe.values())
            no_probe = not probe
            if all_no_frame or no_probe:
                full_coord_seq = []
                coord_lc = 0
                for _cl in range(win_levels):
                    if (_time.time() - t0) >= t_budget * 0.85:
                        break
                    # Per-level re-probe on current game_obj state (the blackboard)
                    try:
                        probe_l = _probe_action_effects(
                            game_obj, ActionInput_cls, available_actions)
                    except Exception:
                        probe_l = {}
                    anf_l = (bool(probe_l) and
                             all(not v.get('frame_changed') for v in probe_l.values()))
                    if probe_l and not anf_l:
                        if verbose:
                            print(f"    [{game_id}] coord-BFS L{_cl + 1}: "
                                  f"action-based level, stopping")
                        break
                    if verbose:
                        print(f"    [{game_id}] coord-BFS L{_cl + 1}: probing coords")
                    sc_c_l, ac_c_l = _probe_coord_effects(
                        game_obj, ActionInput_cls, action_num=6)
                    coords_l = sc_c_l + ac_c_l
                    if coords_l:
                        coords_l = _dedup_coords(game_obj, ActionInput_cls, 6, coords_l)
                    if not coords_l:
                        if verbose:
                            print(f"    [{game_id}] coord-BFS L{_cl + 1}: no coords")
                        break
                    n_cl = len(coords_l)
                    c_nodes_l = min(max(n_cl ** 5, 20000), 400000)
                    if verbose:
                        print(f"    [{game_id}] coord-BFS L{_cl + 1}: "
                              f"{n_cl} coords budget={c_nodes_l}")
                    c_seq_l = _coordinate_bfs(
                        game_obj, ActionInput_cls, 6, coords_l,
                        max_depth=30, max_nodes=c_nodes_l,
                        verbose=verbose, game_id=f"{game_id}/L{_cl + 1}",
                    )
                    if c_seq_l is None:
                        if verbose:
                            print(f"    [{game_id}] coord-BFS L{_cl + 1}: no solution")
                        break
                    # Apply sequence to game_obj in-place (advances to next level)
                    prev_sc_l = getattr(game_obj, '_score', 0)
                    for _st in c_seq_l:
                        _al = getattr(GameAction, f'ACTION{_st["action"]}',
                                      GameAction.ACTION6)
                        _dl = _st.get('data') or {}
                        game_obj.perform_action(ActionInput_cls(id=_al, data=_dl))
                    new_sc_l = getattr(game_obj, '_score', 0)
                    if new_sc_l > prev_sc_l:
                        coord_lc += 1
                        full_coord_seq.extend(c_seq_l)
                        if verbose:
                            print(f"    [{game_id}] coord-BFS L{_cl + 1}: done "
                                  f"(score {prev_sc_l}->{new_sc_l})")
                    else:
                        if verbose:
                            print(f"    [{game_id}] coord-BFS L{_cl + 1}: "
                                  f"no score increment")
                        break

                if full_coord_seq:
                    try:
                        obs2 = env.reset()
                        acts = 0
                        lc = 0
                        for _step in full_coord_seq:
                            _an2 = _step['action']
                            _action2 = getattr(
                                GameAction, f'ACTION{_an2}', GameAction.ACTION6)
                            _data2 = _step.get('data')
                            obs2 = env.step(_action2, data=_data2)
                            acts += 1
                            if obs2 is None:
                                break
                            if obs2.state == GameState.WIN:
                                lc = getattr(obs2, 'levels_completed', lc + 1)
                                sc2 = lc / win_levels if win_levels > 0 else 1.0
                                if sc2 >= 1.0:
                                    if verbose:
                                        print(f"    [{game_id}] coord-BFS full win: "
                                              f"score={sc2:.3f} levels={lc}")
                                    return sc2, lc, acts, full_coord_seq
                                # Level transition - continue
                            elif obs2.state == GameState.GAME_OVER:
                                break
                        if obs2 is not None:
                            lc_f = getattr(obs2, 'levels_completed', lc)
                            sc_f = lc_f / win_levels if win_levels > 0 else 0.0
                            if lc_f > 0 or sc_f > 0:
                                if verbose:
                                    print(f"    [{game_id}] coord-BFS partial: "
                                          f"score={sc_f:.3f} levels={lc_f}")
                                return sc_f, lc_f, acts, full_coord_seq
                    except Exception as _e:
                        if verbose:
                            print(f"    [{game_id}] coord-BFS exec error: {_e}")
"""

assert OLD_TIER_1B in src, (
    f"OLD_TIER_1B not found in Cell 9. "
    f"First 50 chars searched: {repr(OLD_TIER_1B[:50])}"
)
src = src.replace(OLD_TIER_1B, NEW_TIER_1B, 1)

# Update version string
src = src.replace(
    'print("BFS solvers defined: _deepcopy_bfs, _env_iddfs, _mechanic_solve (v59: coord-BFS)")',
    'print("BFS solvers defined: _deepcopy_bfs, _env_iddfs, _mechanic_solve (v60: multi-lvl-coord-BFS)")'
)

# Write back
cell9['source'] = [src]
with open('competition_notebook.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("v60 patch applied!")

checks = [
    'v60: multi-lvl-coord-BFS',
    'Compositional approach: re-classify each level independently',
    'Per-level re-probe on current game_obj state',
    'full_coord_seq',
    'coord_lc',
    'Apply sequence to game_obj in-place',
    'action-based level, stopping',
]
for c in checks:
    found = c in src
    print(f"  {'OK' if found else 'MISSING'}: {c}")

print(f"Cell 9 lines: {len(src.splitlines())}")
