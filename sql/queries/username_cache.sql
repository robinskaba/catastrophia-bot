-- name: UpsertUsername :exec
INSERT INTO
  roblox_username_cache (user_id, username)
VALUES
  ($1, $2)
ON CONFLICT (user_id) DO UPDATE
SET
  username = EXCLUDED.username,
  updated_at = NOW();

-- name: GetCachedUsername :one
SELECT
  *
FROM
  roblox_username_cache
WHERE
  user_id = $1;