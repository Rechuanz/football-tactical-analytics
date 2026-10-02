-- Passes que geram chute (pass_shot_assist) ou gol (pass_goal_assist), ligados ao chute
-- resultante via shot_key_pass_id para obter o xG (usado como xA do passe).
SELECT
    p.id, p.team, p.player, p.pass_recipient, p.minute, p.second,
    p.start_x, p.start_y, p.pass_end_x, p.pass_end_y,
    p.pass_goal_assist AS goal_assist,
    s.shot_statsbomb_xg AS xa,
    s.shot_outcome
FROM events p
LEFT JOIN events s ON s.type = 'Shot' AND s.shot_key_pass_id = p.id
WHERE p.type = 'Pass'
  AND (p.pass_shot_assist OR p.pass_goal_assist)
ORDER BY p.minute, p.second;
