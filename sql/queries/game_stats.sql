-- name: CreateGameStatsRecord :exec
INSERT INTO
  game_stats (playing, visits)
VALUES
  ($1, $2);

-- name: GetLatestGameStats :one
SELECT
  *
FROM
  game_stats
ORDER BY
  recorded_at DESC
LIMIT
  1;