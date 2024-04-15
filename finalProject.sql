CREATE DATABASE IF NOT EXISTS final_project;
USE final_project;

CREATE TABLE IF NOT EXISTS buildings(
	name VARCHAR(64) PRIMARY KEY,
    street_number int,
    street_name VARCHAR(64),
    city VARCHAR(64),
    zipcode int,
    num_floors int,
    campus varchar(64),
    FOREIGN KEY (campus) REFERENCES campuses(name));
    
CREATE TABLE IF NOT EXISTS rooms(
	room_number int,
    capacity int,
    ada boolean,
    projector boolean,
    club_only boolean,
    building  VARCHAR(64),
    FOREIGN KEY (building) REFERENCES buildings(name),
    PRIMARY KEY (room_number, building));

CREATE TABLE IF NOT EXISTS students(
	nuid int PRIMARY KEY,
    name VARCHAR(128));

CREATE TABLE IF NOT EXISTS organizations(
	name VARCHAR(64) PRIMARY KEY,
    type VARCHAR(64));

CREATE TABLE IF NOT EXISTS timeslots(
	room_number int,
    building_name  VARCHAR(64),
    start_hour int,
    FOREIGN KEY (building_name) REFERENCES rooms(building),
    FOREIGN KEY (room_number) REFERENCES rooms(room_number),
    PRIMARY KEY (room_number, building_name, start_hour, end_hour),
    CONSTRAINT valid_hour CHECK (start_hour >= 0 AND start_hour < 24));
    
CREATE TABLE IF NOT EXISTS club_officer(
	nuid int,
    organization_name VARCHAR(64),
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (organization_name) REFERENCES organizations(name),
    PRIMARY KEY (nuid, organization_name));
    
CREATE TABLE IF NOT EXISTS signs_in(
	nuid int,
    booking_id int,
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    PRIMARY KEY (nuid, booking_id));
    
CREATE TABLE IF NOT EXISTS bookings(
	nuid int,
    room_number int,
    building_name  VARCHAR(64),
    start_hour int,
    date date,
    booking_id int AUTO_INCREMENT PRIMARY KEY,
    organization_name VARCHAR(64),
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (room_number) REFERENCES timeslots(room_number),
    FOREIGN KEY (building_name) REFERENCES timeslots(building_name),
    FOREIGN KEY (start_hour) REFERENCES timeslots(start_hour),
    FOREIGN KEY (organization_name) REFERENCES organizations(name),
    PRIMARY KEY (nuid, room_number, building_name, start_hour, date));
	
CREATE TABLE IF NOT EXISTS campuses(
	name VARCHAR(64) PRIMARY KEY,
    grad_only boolean,
    student_population int);