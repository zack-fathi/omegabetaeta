PRAGMA foreign_keys = ON;

CREATE TABLE brothers(
  name VARCHAR(20) NOT NULL,
  uniqname VARCHAR(20) DEFAULT "N/A",
  fullname VARCHAR(40) NOT NULL,
  profile_picture VARCHAR(64) DEFAULT "jawad.jpeg",
  password VARCHAR(128) DEFAULT "password",
  major VARCHAR(40) DEFAULT "N/A",
  job VARCHAR(40) DEFAULT "N/A",
  desc VARCHAR(256) DEFAULT "N/A",
  campus VARCHAR(40) DEFAULT "N/A",
  contacts VARCHAR(64) DEFAULT "N/A",
  cross_time VARCHAR(40) DEFAULT "N/A",
  grad_time VARCHAR(40) DEFAULT "N/A",
  line INTEGER NOT NULL,
  line_num INTEGER NOT NULL,
  lion_name TEXT NOT NULL,
  active BIT DEFAULT 0,
  PRIMARY KEY(name)
);

CREATE TABLE recruits(
  uniqname VARCHAR(20) NOT NULL,
  fullname VARCHAR(40) NOT NULL,
  email VARCHAR(20) NOT NULL, 
  campus VARCHAR(40) NOT NULL,
  line_num INTEGER,
  lion_name TEXT,
  accept BIT DEFAULT 0,
  PRIMARY KEY(uniqname)
);

CREATE TABLE gallery(
    filename VARCHAR(64) NOT NULL,
    desc VARCHAR(256),
    PRIMARY KEY(filename)
);