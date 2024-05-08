PRAGMA foreign_keys = ON;

CREATE TABLE brothers(
  uniqname VARCHAR(20) NOT NULL,
  fullname VARCHAR(40) NOT NULL,
  profile_picture VARCHAR(64) DEFAULT "jawad.jpeg",
  password VARCHAR(128),
  major VARCHAR(40) DEFAULT "N/A",
  desc VARCHAR(256) DEFAULT "N/A",
  campus VARCHAR(40) DEFAULT "N/A",
  contacts VARCHAR(64) DEFAULT "N/A",
  cross_time VARCHAR(40) DEFAULT "N/A",
  grad_time VARCHAR(40) DEFAULT "N/A",
  line VARCHAR(40) NOT NULL,
  PRIMARY KEY(uniqname)
);

CREATE TABLE recruits(
  uniqname VARCHAR(20) NOT NULL,
  fullname VARCHAR(40) NOT NULL,
  email VARCHAR(20) NOT NULL, 
  line VARCHAR(40) NOT NULL,
  cross_time VARCHAR(40) NOT NULL,
  campus VARCHAR(40) NOT NULL,
  PRIMARY KEY(uniqname)
);

CREATE TABLE gallery(
    filename VARCHAR(64) NOT NULL,
    desc VARCHAR(256),
    PRIMARY KEY(filename)
);