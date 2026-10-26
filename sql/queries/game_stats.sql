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

-- name: GetPlayingHistory :many
SELECT
  to_timestamp(
    (floor(extract(epoch FROM recorded_at))::bigint / sqlc.arg(bucket_seconds)::bigint) * sqlc.arg(bucket_seconds)::bigint
  )::timestamptz AS bucket,
  MIN(playing)::int AS min_playing,
  MAX(playing)::int AS max_playing,
  AVG(playing)::float AS avg_playing
FROM
  game_stats
WHERE
  recorded_at >= sqlc.arg(since)::timestamptz
GROUP BY
  1
ORDER BY
  1;

-- name: GetPlayingPeak :one
SELECT
  *
FROM
  game_stats
WHERE
  recorded_at >= $1
ORDER BY
  playing DESC,
  recorded_at DESC
LIMIT
  1;

-- name: GetPlayingLow :one
SELECT
  *
FROM
  game_stats
WHERE
  recorded_at >= $1
ORDER BY
  playing ASC,
  recorded_at DESC
LIMIT
  1;

-- name: GetFirstGameStats :one
SELECT
  *
FROM
  game_stats
ORDER BY
  recorded_at ASC
LIMIT
  1;
