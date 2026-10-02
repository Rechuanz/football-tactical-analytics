-- Carries progressivos (campo StatsBomb 120x80, gol em (120, 40)).
-- Condução que reduz a distância ao gol em >= 10 jardas (~9 m) e termina fora dos
-- 40% defensivos do campo (end_x >= 48), para não contar saídas de bola da defesa.
WITH carries AS (
    SELECT
        id, team, player, minute, second,
        start_x, start_y, carry_end_x, carry_end_y,
        sqrt(pow(120 - start_x, 2)       + pow(40 - start_y, 2))       AS dist_start,
        sqrt(pow(120 - carry_end_x, 2)   + pow(40 - carry_end_y, 2))   AS dist_end
    FROM events
    WHERE type = 'Carry'
      AND carry_end_x IS NOT NULL
)
SELECT *, round(dist_start - dist_end, 1) AS yards_gained
FROM carries
WHERE dist_start - dist_end >= 10
  AND carry_end_x >= 48
ORDER BY minute, second;
