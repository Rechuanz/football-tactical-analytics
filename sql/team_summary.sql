-- Resumo por time (um ou vários jogos). Usa progressive_passes_view e
-- progressive_carries_view já registradas. Gols = chutes com desfecho Goal (sem gol contra).
WITH base AS (
    SELECT team,
           count(DISTINCT match_id) AS matches,
           count(*) FILTER (WHERE type = 'Pass') AS passes,
           count(*) FILTER (WHERE type = 'Pass' AND pass_outcome IS NULL) AS completed_passes,
           count(*) FILTER (WHERE type = 'Shot' AND period < 5) AS shots,
           count(*) FILTER (WHERE type = 'Shot' AND period < 5 AND shot_outcome = 'Goal') AS goals,
           round(sum(shot_statsbomb_xg) FILTER (WHERE type = 'Shot' AND period < 5), 2) AS xg,
           round(sum(shot_statsbomb_xg) FILTER (WHERE type = 'Shot' AND period < 5
                                                  AND shot_type <> 'Penalty'), 2) AS npxg
    FROM events WHERE team IS NOT NULL GROUP BY team
),
pp AS (SELECT team, count(*) AS progressive_passes FROM progressive_passes_view GROUP BY team),
pc AS (SELECT team, count(*) AS progressive_carries FROM progressive_carries_view GROUP BY team)
SELECT b.team, b.matches, b.goals, b.shots,
       coalesce(b.xg, 0) AS xg, coalesce(b.npxg, 0) AS npxg,
       b.passes, round(100.0 * b.completed_passes / nullif(b.passes, 0), 1) AS pass_pct,
       coalesce(pp.progressive_passes, 0)  AS progressive_passes,
       coalesce(pc.progressive_carries, 0) AS progressive_carries
FROM base b
LEFT JOIN pp USING (team)
LEFT JOIN pc USING (team)
ORDER BY npxg DESC;
