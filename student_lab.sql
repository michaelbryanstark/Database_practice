DROP TABLE IF EXISTS Enrollment;

DROP TABLE IF EXISTS Departments;

DROP TABLE IF EXISTS Students;

DROP TABLE IF EXISTS Courses;

CREATE TABLE Courses (
    courseId INT NOT NULL PRIMARY KEY,
    courseName VARCHAR(50),
    courseCode INT NOT NULL,
    creditHours INT NOT NULL,
    departmentId INT,
    FOREIGN KEY (departmentId) REFERENCES Departments (id)
);

CREATE TABLE Students (
    studentId INT NOT NULL PRIMARY KEY,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    createdAt DATE DEFAULT CURRENT_DATE
);

CREATE TABLE Departments (
    departmentId INT NOT NULL PRIMARY KEY,
    departmentName VARCHAR(50) NOT NULL
);

CREATE TABLE Enrollment (
    courseId INT,
    studentId INT,
    FOREIGN KEY (courseId) REFERENCES Courses (id),
    FOREIGN KEY (studentId) REFERENCES Students (id)
);