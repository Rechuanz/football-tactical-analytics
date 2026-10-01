-- Passes progressivos (definição estilo Wyscout, campo StatsBomb 120x80, gol em (120, 40)).
-- Passe completo (pass_outcome nulo), em jogo corrido, que reduz a distância ao gol em:
--   >= 30% se origem e destino estão no próprio campo
--   >= 15% se cruza o meio-campo
--   >= 10% se origem e destino estão no campo adversário
-- Passes que terminam dentro da área também contam se avançam >= 10 jardas.
WITH passes AS (
    SELECT
        id, team, player, pass_recipient, minute, second,
        start_x, start_y, pass_end_x, pass_end_y,
        sqrt(pow(120 - start_x, 2)    + pow(40 - start_y, 2))    AS dist_start,
        sqrt(pow(120 - pass_end_x, 2) + pow(40 - pass_end_y, 2)) AS dist_end
    FROM events
    WHERE type = 'Pass'
      AND pass_outcome IS NULL
      AND play_pattern = 'Regular Play'
      AND pass_end_x IS NOT NULL
      AND start_x < 120
)
SELECT
    *,
    round(1 - dist_end / dist_start, 3) AS dist_reduction
FROM passes
WHERE pass_end_x > start_x
  AND (
        (start_x <  60 AND pass_end_x <  60 AND dist_end <= 0.70 * dist_start)
     OR (start_x <  60 AND pass_end_x >= 60 AND dist_end <= 0.85 * dist_start)
     OR (start_x >= 60 AND pass_end_x >= 60 AND dist_end <= 0.90 * dist_start)
  )
ORDER BY minute, second;
