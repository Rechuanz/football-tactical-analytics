-- Resumo por jogador sobre vários jogos. Usa os resultados das outras queries,
-- registrados como views: progressive_passes_view, progressive_carries_view,
-- shot_participation_view. Normalização por jogo disputado (aparições, não minutos).
WITH appearances AS (
    SELECT team, player, any_value(player_label) AS player_label,
           count(DISTINCT match_id) AS matches
    FROM events WHERE player IS NOT NULL GROUP BY ALL
),
pp AS (SELECT team, player, count(*) AS progressive_passes
       FROM progressive_passes_view GROUP BY ALL),
pc AS (SELECT team, player, count(*) AS progressive_carries
       FROM progressive_carries_view GROUP BY ALL)
SELECT
    a.team, a.player, a.player_label, a.matches,
    coalesce(pp.progressive_passes, 0)  AS progressive_passes,
    coalesce(pc.progressive_carries, 0) AS progressive_carries,
    coalesce(sp.shots, 0) AS shots, coalesce(sp.goals, 0) AS goals,
    coalesce(sp.xg, 0) AS xg, coalesce(sp.npxg, 0) AS npxg, coalesce(sp.key_passes, 0) AS key_passes,
    coalesce(sp.assists, 0) AS assists, coalesce(sp.xa, 0) AS xa,
    coalesce(sp.xg_plus_xa, 0) AS xg_plus_xa,
    coalesce(sp.npxg_plus_xa, 0) AS npxg_plus_xa,
    round(coalesce(sp.npxg_plus_xa, 0) / a.matches, 2) AS npxg_xa_per_match,
    round((coalesce(pp.progressive_passes, 0) + coalesce(pc.progressive_carries, 0))
          / a.matches, 1) AS progressions_per_match
FROM appearances a
LEFT JOIN pp USING (team, player)
LEFT JOIN pc USING (team, player)
LEFT JOIN shot_participation_view sp USING (team, player)
ORDER BY npxg_plus_xa DESC, progressive_passes DESC;
