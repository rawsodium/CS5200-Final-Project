CREATE DATABASE IF NOT EXISTS final_project;
USE final_project;

-- TODOS: finish procedures/functions
--        make sure FKs have ON UPDATE and ON DELETE
--        make sure field and table constraints are correct

-- TABLES
CREATE TABLE IF NOT EXISTS campuses(
	name VARCHAR(64) PRIMARY KEY,
    grad_only TINYINT,
    student_population int);
    
CREATE TABLE IF NOT EXISTS buildings(
	name VARCHAR(64) PRIMARY KEY,
    street_number int,
    street_name VARCHAR(64),
    city VARCHAR(64),
    zipcode int,
    num_floors int,
    campus VARCHAR(64),
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

-- starts empty
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
	FOREIGN KEY (room_number) REFERENCES rooms(room_number),
    FOREIGN KEY (building_name) REFERENCES rooms(building),
    PRIMARY KEY (room_number, building_name, start_hour),
    CONSTRAINT valid_hour CHECK (start_hour >= 0 AND start_hour < 24));

-- Starts empty
CREATE TABLE IF NOT EXISTS club_officer(
	nuid int,
    organization_name VARCHAR(64),
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (organization_name) REFERENCES organizations(name),
    PRIMARY KEY (nuid, organization_name));

-- Starts empty
CREATE TABLE IF NOT EXISTS bookings(
	nuid int,
    room_number int,
    building_name  VARCHAR(64),
    start_hour int,
    date date,
    booking_id int AUTO_INCREMENT PRIMARY KEY,
    organization_name VARCHAR(64),
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (room_number, building_name, start_hour) REFERENCES timeslots(room_number, building_name, start_hour));

-- starts empty
CREATE TABLE IF NOT EXISTS signs_in(
	nuid int NOT NULL,
    booking_id int,
    FOREIGN KEY (nuid) REFERENCES students(nuid),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    PRIMARY KEY (booking_id));
    
    
-- DATABASE PROCEDURES AND FUNCTIONS

-- validate_student: Given a user's NUID, Check if their NUID is in the Students table
-- usage: we check if there is at least one row returned from this procedure on the frontend
DROP PROCEDURE IF EXISTS validate_student;
DELIMITER $$
CREATE PROCEDURE validate_student(nuid INT)
BEGIN
	SELECT * FROM students
        WHERE students.nuid = nuid;
END$$
DELIMITER ;

-- get_user_bookings: Given a user's NUID, return all bookings associated with them
DROP PROCEDURE IF EXISTS get_user_bookings;
DELIMITER $$
CREATE PROCEDURE get_user_bookings(nuid INT)
BEGIN
	SELECT * FROM bookings WHERE bookings.nuid = nuid;
END$$
DELIMITER ;

-- update_booking: Given a booking number, update the booking's date or time (or both!)
-- Will need to account for the cases in which a user tries to do one of the following:
-- 1) Update to an invalid time (not between 0 and 23)
-- 2) Update to an invalid time (held by another booking in the same room/same day, aka overwriting someone else's booking)
-- 3) Update to an invalid day (?)
-- Need to use the does_booking_exist function to check if a booking already exists for the given day and time

-- TODO: this still needs work I think
DROP PROCEDURE IF EXISTS update_booking;
DELIMITER $$
CREATE PROCEDURE update_booking(booking_num INT, booking_date DATE, booking_time INT)
BEGIN
	-- If both date and time are provided, update both fields
	IF booking_date IS NOT NULL AND booking_time IS NOT NULL THEN
		UPDATE bookings SET date = booking_date
			WHERE bookings.booking_id = booking_num;
		UPDATE bookings SET start_hour = booking_time
			WHERE bookings.booking_id = booking_num;
	-- If a time is not provided but a date is, update the date only
	ELSEIF booking_date IS NOT NULL AND booking_time IS NULL THEN
		UPDATE bookings SET date = booking_date
			WHERE bookings.booking_id = booking_num;
	-- If a time is provided but a date is not, update the time only
	ELSEIF booking_date IS NULL AND booking_time IS NOT NULL THEN
		UPDATE bookings SET start_hour = booking_time
			WHERE bookings.booking_id = booking_num;
    END IF;
END $$
DELIMITER ;

-- display_other_times: given a booking number display other days and times that the room is available
DROP PROCEDURE IF EXISTS display_other_times;
DELIMITER $$
CREATE PROCEDURE display_other_times(booking_num INT)
BEGIN
    -- get the booking's room number and building name
    DECLARE room_num INT;
    DECLARE building_name VARCHAR(64);
    SELECT room_number, building_name INTO room_num, building_name FROM bookings WHERE booking_id = booking_num;
    
    -- get all timeslots for the room that are not booked
    SELECT * FROM timeslots AS available_timeslots
        WHERE NOT EXISTS (SELECT * FROM bookings 
                            WHERE bookings.room_number = available_timeslots.room_number 
                                AND bookings.building_name = available_timeslots.building_name 
                                    AND bookings.start_hour = available_timeslots.start_hour
                                        AND bookings.date = available_timeslots.date);
END $$
DELIMITER ;

-- does_booking_exist: Checks if a booking has been made on a certain day and time for a given room
-- usage: returns TRUE if a booking for the room (name and number) for a given data and time exists, FALSE otherwise
DROP FUNCTION IF EXISTS does_booking_exist;
DELIMITER $$
CREATE FUNCTION does_booking_exist(day DATE, time INT, building_name VARCHAR(64), room_number INT)
    RETURNS BOOL DETERMINISTIC
    READS SQL DATA
    BEGIN
        DECLARE num_rows INT;
        SELECT COUNT(*) INTO num_rows FROM bookings
            WHERE (date = day AND start_hour = time AND building_name = building_name AND room_number = room_number);
        RETURN num_rows > 0;
    END $$
DELIMITER ;

-- find_room_with_criteria: Given criteria (capacity, ADA compliant, start time, date, projector, and club association), finds all
-- rooms that satisfy the user's wants
DROP PROCEDURE IF EXISTS find_room_with_criteria;
DELIMITER $$
CREATE PROCEDURE find_room_with_criteria(cap INT, ada BOOL, time INT, day DATE, projector BOOL, club BOOL)
BEGIN
	-- first, get compliant rooms
	SELECT * FROM rooms AS compliant_rooms
        WHERE (capacity = cap AND rooms.ada = ada AND rooms.projector = projector AND club_association = club); 
	
    -- then, get compliant timeslots
    SELECT * FROM timeslots AS compliant_timeslots
        WHERE start_hour = time;
    
    -- join compliant rooms to compliant timeslots
    SELECT * FROM compliant_timeslots AS joined_rooms_timeslots
        JOIN compliant_rooms
            ON compliant_timeslots.room_number = compliant_rooms.room_number;
    
    -- somehow: check if the room/timeslot has already been booked with does_booking_exist
    -- if yes, then remove those records from the results we return to the user
    SELECT * FROM joined_rooms_timeslots AS available_rooms_timeslots
        WHERE NOT does_booking_exist(day, time, joined_rooms_timeslots.building, joined_rooms_timeslots.room_number);
END $$
DELIMITER ;

-- is_valid_club: Checks if the given club organization name is registered in the database, otherwise a user should not be able to book a room for a club that doesn't exist
-- usage: returns TRUE if the club is valid, FALSE otherwise
DROP FUNCTION IF EXISTS is_valid_club;
DELIMITER $$
CREATE FUNCTION is_valid_club(club_name VARCHAR(64))
    RETURNS BOOL DETERMINISTIC
    READS SQL DATA
    BEGIN
        DECLARE num_rows INT;
        SELECT COUNT(*) INTO num_rows FROM organizations WHERE name = club_name;
        RETURN num_rows > 0;
    END $$
DELIMITER ;

-- is_officer_of_club: Checks if the given student is a club officer for the club they want to book a room for
-- -- usage: returns TRUE if the student is an officer, FALSE otherwise
DROP FUNCTION IF EXISTS is_officer_of_club;
DELIMITER $$
CREATE FUNCTION is_officer_of_club(user_nuid INT, club_name VARCHAR(64))
    RETURNS BOOL DETERMINISTIC
    READS SQL DATA
    BEGIN
        DECLARE num_rows INT;
        SELECT COUNT(*) INTO num_rows FROM club_officer WHERE (nuid = user_nuid AND organization_name = club_name);
        RETURN num_rows > 0;
    END $$
DELIMITER ;

-- create_booking: Add a new row in the bookings table
-- TODO: update timeslots table to reflect availibility change...?
-- TODO: make sure club user enters is a valid club... -> using is_valid_club
-- TODO (?): make sure user is a club officer if they are trying to book for a club?? -> using is_officer_of_club
DROP PROCEDURE IF EXISTS create_booking;
DELIMITER $$
CREATE PROCEDURE create_booking(user_nuid INT, r_num INT, b_name VARCHAR(64), s_hour INT, day DATE, org_name VARCHAR(64))
BEGIN
    -- id of last row for inserting into bookings table
    DECLARE last_booking_id INT DEFAULT -1;
	-- error handler, just in case
	DECLARE duplicate_entry_for_key TINYINT DEFAULT FALSE;
	DECLARE EXIT HANDLER FOR 1062
		SET duplicate_entry_for_key = TRUE;
        
	-- get last booking_id inserted into table
    SELECT MAX(booking_id) FROM bookings INTO last_booking_id;
        
	-- you would think that creating a new tuple would autoincrement the id, but who even knows - hence why i used the last inserted id as a reference point.
	INSERT INTO bookings(nuid, room_number, building_name, start_hour, date, organization_name)
		VALUES(user_nuid, r_num, b_name, s_hour, day, last_booking_id + 1, org_name);
            
	IF duplicate_entry_for_key = TRUE THEN
		SELECT 'Row was not inserted - duplicate key encountered.'
			AS message;
		SIGNAL SQLSTATE '23000' SET MESSAGE_TEXT = 'Row not inserted - duplicate key encountered.';
	ELSE
		SELECT '1 row was inserted';
	END IF;
END $$
DELIMITER ;

-- delete_booking: Given a booking number, deletes it from the bookings table if it has not been signed into yet
DROP PROCEDURE IF EXISTS delete_booking;
DELIMITER $$
CREATE PROCEDURE delete_booking(booking_num INT)
BEGIN
	-- delete from the bookings table if not in signs_in
    DELETE FROM bookings
        WHERE booking_id = booking_num
        AND booking_num NOT IN (SELECT booking_id FROM signs_in);
END $$
DELIMITER ;

-- validate_booking_num: Checks if the booking number exists for the given user
-- usage: check if it returns a row on the frontend
DROP PROCEDURE IF EXISTS validate_booking_num;
DELIMITER $$
CREATE PROCEDURE validate_booking_num(booking_num INT)
BEGIN
	SELECT * FROM bookings WHERE booking_id = booking_num;
END $$
DELIMITER ;

-- check_into_room: Inserts a tuple into the signs_in table, signaling that a booking has been signed into
DROP PROCEDURE IF EXISTS check_into_room;
DELIMITER $$
CREATE PROCEDURE check_into_room(booking_num INT, user_nuid INT)
BEGIN
	INSERT INTO signs_in(nuid, booking_id)
		VALUES(user_nuid, booking_num);
        
	IF booking_num IN (SELECT * FROM signs_in) THEN
		SELECT 'Row was not inserted - booking already checked into.'
			AS message;
		SIGNAL SQLSTATE '23000' SET MESSAGE_TEXT = 'Row not inserted - booking already checked into.';
	ELSE
		SELECT '1 row was inserted';
	END IF;
END $$
DELIMITER ;

-- create_user: given a name and nuid, create a new user
DROP PROCEDURE IF EXISTS create_user;
DELIMITER $$
CREATE PROCEDURE create_user(user_name VARCHAR(128), user_nuid INT)
BEGIN
    IF NOT EXISTS (SELECT * FROM students WHERE nuid = user_nuid) THEN
        INSERT INTO students(name, nuid)
            VALUES(user_name, user_nuid);
    END IF;
END $$
DELIMITER ;

-- add_club_officer: given a user's nuid and a club name, add the user as an officer of the club
-- we only want to add the user if they are not already an officer of the club
DROP PROCEDURE IF EXISTS add_club_officer;
DELIMITER $$
CREATE PROCEDURE add_club_officer(user_nuid INT, club_name VARCHAR(64))
BEGIN
    INSERT INTO club_officer(nuid, organization_name)
        VALUES(user_nuid, club_name);
END $$
DELIMITER ;