-- Arestas da rede de passes: passes completos por par (passador -> recebedor), não
-- direcionado (A-B e B-A somados), até a primeira substituição do time.
WITH first_sub AS (
    SELECT team, min(index) AS sub_index
    FROM events WHERE type = 'Substitution' GROUP BY team
)
SELECT p.team,
       least(p.player, p.pass_recipient)    AS player_a,
       greatest(p.player, p.pass_recipient) AS player_b,
       count(*) AS passes
FROM events p
LEFT JOIN first_sub f USING (team)
WHERE p.type = 'Pass'
  AND p.pass_outcome IS NULL
  AND p.pass_recipient IS NOT NULL
  AND p.index < coalesce(f.sub_index, 1e9)
GROUP BY ALL
HAVING count(*) >= 3
ORDER BY p.team, passes DESC;
