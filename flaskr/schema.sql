CREATE TABLE Person (
type INT,
username VARCHAR(100) PRIMARY KEY,
password VARCHAR(100),
email VARCHAR(100)
);

CREATE TABLE Question (
question_tag VARCHAR(1000),
question_id INTEGER PRIMARY KEY AUTOINCREMENT,
question_text VARCHAR(1000),
question_date DATE,
question_time TIME,
question_confusion INT
);

CREATE TABLE Class (
class_name VARCHAR(100) PRIMARY KEY,
class_key INT,
class_admin VARCHAR(1000) 
);

CREATE TABLE Asks (
question_id INTEGER PRIMARY KEY,
username VARCHAR(100),
FOREIGN KEY(question_id)
REFERENCES Question(question_id)
ON DELETE CASCADE,
FOREIGN KEY(username)
REFERENCES Person(username)
ON DELETE CASCADE
);

CREATE TABLE Subscribes (
username VARCHAR(100),
class_name VARCHAR(100),
PRIMARY KEY(username, class_name),
FOREIGN KEY(class_name)
REFERENCES Class(class_name)
ON DELETE CASCADE
ON UPDATE CASCADE,
FOREIGN KEY(username)
REFERENCES Person(username)
ON DELETE CASCADE
);

CREATE TABLE Asked_in (
question_id INTEGER PRIMARY KEY,
class_name VARCHAR(100),
FOREIGN KEY(class_name)
REFERENCES Class(class_name)
ON DELETE CASCADE
ON UPDATE CASCADE,
FOREIGN KEY(question_id)
REFERENCES Question(question_id)
ON DELETE CASCADE
);
