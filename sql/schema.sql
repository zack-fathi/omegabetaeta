PRAGMA foreign_keys = ON;

CREATE TABLE lion_names(
  lion_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  meaning TEXT DEFAULT ''
);

CREATE TABLE brothers(
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(20) NOT NULL UNIQUE,
  uniqname VARCHAR(20) DEFAULT "N/A",
  fullname VARCHAR(40) NOT NULL,
  profile_picture VARCHAR(64) DEFAULT "default.jpg",
  password VARCHAR(128) DEFAULT "password",
  major VARCHAR(40) DEFAULT "N/A",
  job VARCHAR(40) DEFAULT "N/A",
  desc VARCHAR(256) DEFAULT "N/A",
  campus VARCHAR(40) DEFAULT "N/A",
  contacts VARCHAR(64) DEFAULT "N/A",
  cross_time VARCHAR(40) DEFAULT "N/A",
  grad_time DATE DEFAULT NULL,
  line INTEGER NOT NULL,
  line_num INTEGER NOT NULL,
  lion_name_id INTEGER,
  active BIT DEFAULT 0,
  default_password TEXT DEFAULT NULL,
  password_changed BIT DEFAULT 0,
  email_sent BIT DEFAULT 0,
  FOREIGN KEY (lion_name_id) REFERENCES lion_names(lion_name_id)
);

CREATE TABLE recruits(
  uniqname VARCHAR(20) NOT NULL,
  fullname VARCHAR(40) NOT NULL,
  email VARCHAR(20) NOT NULL, 
  campus VARCHAR(40) NOT NULL,
  line_num INTEGER,
  lion_name_id INTEGER,
  accept BIT DEFAULT 0,
  deleted BIT DEFAULT 0,
  PRIMARY KEY(uniqname),
  FOREIGN KEY (lion_name_id) REFERENCES lion_names(lion_name_id)
);

CREATE TABLE gallery(
    filename VARCHAR(64) NOT NULL,
    desc VARCHAR(256),
    sort_order INTEGER DEFAULT 0,
    carousel BIT DEFAULT 0,
    carousel_focus INTEGER DEFAULT 50,
    PRIMARY KEY(filename)
);

CREATE TABLE change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    change_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    desc TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES brothers(user_id)
);


CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES brothers(user_id) ON UPDATE SET NULL ON DELETE SET NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE message_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    reply_text TEXT NOT NULL,
    replied_by INTEGER NOT NULL,
    replied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (replied_by) REFERENCES brothers(user_id)
);
