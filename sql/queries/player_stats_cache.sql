-- name: UpsertPlayerStatsCache :exec
INSERT INTO
  player_stats_cache (user_id, stats)
VALUES
  ($1, $2)
ON CONFLICT (user_id) DO UPDATE
SET
  stats = EXCLUDED.stats,
  refreshed_at = NOW();

-- name: GetPlayerStatsCache :one
SELECT
  *
FROM
  player_stats_cache
WHERE
  user_id = $1;