CREATE TABLE IF NOT EXISTS stats_searches (
  id SERIAL PRIMARY KEY,
  discord_id INTEGER,
  rbx_username VARCHAR(3,20)
);

CREATE TABLE IF NOT EXISTS creators (
  discord_id INTEGER PRIMARY KEY,
  since REAL
);