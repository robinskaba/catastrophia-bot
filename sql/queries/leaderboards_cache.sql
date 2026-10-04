-- name: UpsertLeaderboardsCache :exec
INSERT INTO
  leaderboards_cache (period, leaderboard_data)
VALUES
  ($1, $2)
ON CONFLICT (period) DO UPDATE
SET
  leaderboard_data = EXCLUDED.leaderboard_data,
  refreshed_at = NOW();

-- name: GetLeaderboardsCache :one
SELECT
  *
FROM
  leaderboards_cache
WHERE
  period = $1;