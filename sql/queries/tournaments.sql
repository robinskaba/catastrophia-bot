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
  (
    server_code = $1
    AND scheduled_at = $2
  );

-- name: UpdateTournamentState :exec
UPDATE scheduled_tournaments
SET
  state = $2
WHERE
  id = $1;
