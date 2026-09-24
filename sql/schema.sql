CREATE TABLE IF NOT EXISTS creators (discord_id BIGINT PRIMARY KEY, since REAL);

CREATE TABLE IF NOT EXISTS command_usage (
  id SERIAL PRIMARY KEY,
  command_name TEXT NOT NULL,
  discord_id BIGINT NOT NULL,
  arguments JSONB DEFAULT '{}'::jsonb,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roblox_username_cache (
  user_id BIGINT PRIMARY KEY,
  username TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);