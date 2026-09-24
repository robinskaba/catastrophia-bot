-- name: AddCommandUsage :exec
INSERT INTO
  command_usage (command_name, discord_id, arguments)
VALUES
  ($1, $2, $3);

-- name: GetSearchedStatsUsernamesByDiscordId :many
SELECT
  arguments ->> 'username' AS username,
  COUNT(*) AS search_count
FROM
  command_usage
WHERE
  discord_id = $1
  AND command_name = 'stats'
  AND arguments ->> 'username' IS NOT NULL
GROUP BY
  arguments ->> 'username'
ORDER BY
  search_count DESC
LIMIT
  $2;
