-- Participação em finalizações por jogador: chutes, xG e np-xG (sem pênaltis) próprios
-- (sem disputa de pênaltis, period 5) + passes-chave, assistências e xA.
WITH shots AS (
    SELECT team, player, count(*) AS shots, round(sum(shot_statsbomb_xg), 2) AS xg,
           round(sum(shot_statsbomb_xg) FILTER (WHERE shot_type <> 'Penalty'), 2) AS npxg,
           count(*) FILTER (WHERE shot_outcome = 'Goal') AS goals
    FROM events
    WHERE type = 'Shot' AND period < 5
    GROUP BY team, player
),
key_passes AS (
    SELECT p.team, p.player, count(*) AS key_passes,
           count(*) FILTER (WHERE p.pass_goal_assist) AS assists,
           round(sum(s.shot_statsbomb_xg), 2) AS xa
    FROM events p
    LEFT JOIN events s ON s.type = 'Shot' AND s.shot_key_pass_id = p.id
    WHERE p.type = 'Pass' AND (p.pass_shot_assist OR p.pass_goal_assist)
    GROUP BY p.team, p.player
)
SELECT team, player,
       coalesce(shots, 0) AS shots, coalesce(goals, 0) AS goals, coalesce(xg, 0) AS xg, coalesce(npxg, 0) AS npxg,
       coalesce(key_passes, 0) AS key_passes, coalesce(assists, 0) AS assists,
       coalesce(xa, 0) AS xa,
       round(coalesce(xg, 0) + coalesce(xa, 0), 2) AS xg_plus_xa,
       round(coalesce(npxg, 0) + coalesce(xa, 0), 2) AS npxg_plus_xa
FROM shots FULL JOIN key_passes USING (team, player)
ORDER BY npxg_plus_xa DESC;
