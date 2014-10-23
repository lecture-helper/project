CREATE TABLE Class (
class_name VARCHAR(100) PRIMARY KEY,
class_key INT 
);

CREATE TABLE Question (
question_id INT PRIMARY KEY,
question_text VARCHAR(1000),
question_date DATE,
question_time TIME 
);

CREATE TABLE Asked_in (
question_id INT,
class_name VARCHAR(100) ,
PRIMARY KEY(question_id, class_name)
);
