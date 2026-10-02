-- Chutes (sem disputa de pênaltis, period 5) com localização, xG e desfecho.
SELECT
    id, team, player, player_label, minute, second,
    start_x AS x, start_y AS y,
    shot_statsbomb_xg AS xg,
    shot_outcome,
    shot_outcome = 'Goal' AS is_goal,
    shot_type = 'Penalty' AS is_penalty
FROM events
WHERE type = 'Shot' AND period < 5 AND start_x IS NOT NULL
ORDER BY minute, second;
