CREATE DATABASE attendance_db;

USE attendance_db;

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(50),
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    department VARCHAR(255),
    designation VARCHAR(255),
    password_hash VARCHAR(255),
    face_encoding LONGTEXT,
    leave_balance INT DEFAULT 0,
    total_leaves INT DEFAULT 0,
    remaining_leaves INT DEFAULT 0,
    extra_leaves INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    in_date DATE NOT NULL,
    in_time DATETIME,
    out_time DATETIME,
    latitude DOUBLE,
    longitude DOUBLE,
    method VARCHAR(20),
    match_distance DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_employee_date (employee_id, in_date),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at DATETIME
);

CREATE TABLE leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    applied_at DATETIME,
    approved_at DATETIME,
    approved_by VARCHAR(50),
    total_days INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT(1) DEFAULT 0
);

CREATE TABLE leave_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(50) NOT NULL,
    total_leaves INT DEFAULT 0,
    used_leaves INT DEFAULT 0,
    extra_leaves INT DEFAULT 0,
    remaining_leaves INT DEFAULT 0,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);
