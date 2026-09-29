-- name: CreateGameStatsRecord :exec
INSERT INTO
  game_stats (playing, visits)
VALUES
  ($1, $2);