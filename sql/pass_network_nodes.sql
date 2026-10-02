-- Nós da rede de passes: posição média (start_x/y) dos passes de cada jogador e
-- número de passes, até a primeira substituição do time (formação inicial).
WITH first_sub AS (
    SELECT team, min(index) AS sub_index
    FROM events WHERE type = 'Substitution' GROUP BY team
)
SELECT p.team, p.player, any_value(p.player_label) AS player_label,
       avg(p.start_x) AS x, avg(p.start_y) AS y, count(*) AS passes
FROM events p
LEFT JOIN first_sub f USING (team)
WHERE p.type = 'Pass'
  AND p.index < coalesce(f.sub_index, 1e9)
  AND p.period < 5
GROUP BY p.team, p.player
HAVING count(*) >= 3
ORDER BY p.team, passes DESC;
