-- name: AddCreator :one
INSERT INTO
  creators (discord_id, since)
VALUES
  ($1, $2)
RETURNING
  *;

-- name: GetCreator :one
SELECT
  *
FROM
  creators
WHERE
  discord_id = $1;