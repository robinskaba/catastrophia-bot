CREATE TABLE IF NOT EXISTS stats_searches (
  id SERIAL PRIMARY KEY,
  discord_id INTEGER,
  rbx_username VARCHAR(3,20)
);