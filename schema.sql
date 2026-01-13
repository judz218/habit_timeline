PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS habit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  first_action TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS habit_step (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  habit_id INTEGER NOT NULL,
  parent_step_id INTEGER NULL,
  title TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  FOREIGN KEY (habit_id) REFERENCES habit(id) ON DELETE CASCADE,
  FOREIGN KEY (parent_step_id) REFERENCES habit_step(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS day_plan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plan_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day_plan_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  scheduled_time TEXT NULL, -- HH:MM
  sort_order INTEGER NOT NULL,
  source_habit_id INTEGER NULL,
  source_step_id INTEGER NULL,
  parent_item_id INTEGER NULL,
  done_at TEXT NULL,
  FOREIGN KEY (day_plan_id) REFERENCES day_plan(id) ON DELETE CASCADE,
  FOREIGN KEY (source_habit_id) REFERENCES habit(id) ON DELETE SET NULL,
  FOREIGN KEY (source_step_id) REFERENCES habit_step(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_plan_item_day ON plan_item(day_plan_id);
CREATE INDEX IF NOT EXISTS idx_habit_step_habit ON habit_step(habit_id);
