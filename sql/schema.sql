-- GENERAL
CREATE TABLE IF NOT EXISTS creators (discord_id BIGINT PRIMARY KEY, since REAL);

CREATE TABLE IF NOT EXISTS scheduled_tournaments (
  id SERIAL PRIMARY KEY,
  server_code INT NOT NULL,
  scheduled_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ,
  state INT NOT NULL DEFAULT 0,
  UNIQUE (server_code, scheduled_at)
);

-- TRACKING
CREATE TABLE IF NOT EXISTS command_usage (
  id SERIAL PRIMARY KEY,
  command_name TEXT NOT NULL,
  discord_id BIGINT NOT NULL,
  arguments JSONB DEFAULT '{}'::jsonb,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_stats (
  id SERIAL PRIMARY KEY,
  playing INT NOT NULL,
  visits INT NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recorded_at ON game_stats (recorded_at);

-- CACHES
CREATE TABLE IF NOT EXISTS roblox_username_cache (
  user_id BIGINT PRIMARY KEY,
  username TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leaderboards_cache (
  period TEXT PRIMARY KEY, -- '2026', '09_2026'
  leaderboard_data JSONB NOT NULL,
  refreshed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP -- useful if a player's stats get migrated
);