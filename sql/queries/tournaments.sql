-- name: AddScheduledTournament :exec
INSERT INTO
  scheduled_tournaments (server_code, scheduled_at, ends_at, state)
VALUES
  (
    $1,
    $2,
    sqlc.narg ('ends_at'),
    sqlc.narg ('state')
  );

-- name: GetTournamentById :one
SELECT
  *
FROM
  scheduled_tournaments
WHERE
  id = $1
LIMIT
  1;

-- name: GetUpcomingOrOngoingTournaments :many
SELECT
  *
FROM
  scheduled_tournaments
WHERE
  state = 0
  OR state = 1;

-- name: DeleteScheduledTournament :exec
DELETE FROM scheduled_tournaments
WHERE
  id = $1;

-- name: UpdateTournamentState :exec
UPDATE scheduled_tournaments
SET
  state = $2
WHERE
  id = $1;
