#!usr/bin/env python
import pymysql
import getpass as gp

# variables for state management
nuid = -1
global_flag = True
not_connected_to_db = True
validated_flag = False
counter = 0

# CRUD functions, and various other helper functions

# Utility function to check that an UPDATE, INSERT or DELETE operation was successful
# Returns True if the procedure updates the rows needed, False otherwise
def check_rows_affected(cur) -> bool:
    affected_rows = cur.rowcount
    return affected_rows > 0


# Convert yes/no responses to boolean values
def yn_to_bool(choice: str) -> bool:
    return choice.lower() == 'yes'


# Creates an entry in the student table
# Returns 0 if the student was successfully added, -1 otherwise
def create_user(cxn, nuid: int, name: str) -> int:
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure create_user
        try:
            cur.callproc('create_user', [name, nuid])
        except:
            print("Error creating user. Please try again.\n")
            cxn.rollback()

        # we check rows affected to make sure insert worked (or not)
        if check_rows_affected(cur):
            # commit change
            cxn.commit()
            cur.close()
            return 0
        else:
            print("Error in creating user.\n")
            return -1
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1


# Add a club association 
# Returns 0 if the student was successfully added, -1 otherwise
def add_club_officer(cxn, nuid: int, club_name: str) -> int: 
    try:
        # create cursor
        cur = cxn.cursor()

        # call DB procedure add_club_officer
        try:
            cur.callproc('add_club_officer', [nuid, club_name])
        except:
            # because apparently, you can't add a new user and then add a club to them within the same session...
            print("Error adding club association. Please try again.\n")
            cxn.rollback()

        # we check rows affected
        if check_rows_affected(cur):
            # commit change
            cxn.commit()
            cur.close()
            return 0
        else:
            print("Error in updating club association.\n")
            return -1
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1


# Validate a user's entered NUID
# Returns True if the user's NUID is in the data, False otherwise
def validate_nuid(cxn, nuid: int) -> bool:
    res_rows = []
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure validate_student
        cur.callproc('validate_student', [nuid])
        res_rows = cur.fetchall()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
    # If we return no rows, student doesn't exist
    return len(res_rows) > 0


# Validates a user's entered booking number
# Returns True if the booking exists for the given student, False otherwise
def validate_booking_num(cxn, booking_num: int) -> bool:
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure to check if booking num in user's list of bookings
        cur.callproc('validate_booking_num', [booking_num])
        cxn.commit()
        affected_rows = cur.rowcount
        cur.close()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
    return affected_rows > 0
    

# Returns a list of the bookings associated with their NUID that they signed in with
def view_bookings(cxn) -> list:
    returned_rows = []
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure get_user_bookings
        cur.callproc('get_user_bookings', [nuid])
        returned_rows = cur.fetchall()
        cur.close()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
    return returned_rows

# Returns a list of the other available days/timeslots for a given room, based on the booking number
# originally provided by the user
def display_other_bookings(cxn, booking_num: int) -> list:
    returned_rows = []
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure display_other_times
        cur.callproc('display_other_times', [booking_num])
        returned_rows = cur.fetchmany(size=15)
        cur.close()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
    return returned_rows

# Updates a user's booking based on the criteria entered (either update date, time, or both)
# Returns 0 upon success of operation, and -1 on error
def update_booking(cxn, booking_num: int, date: str, timeslot: int) -> int:
    try:
        # create cursor
        cur = cxn.cursor()
        # validate booking number, exit if error
        if validate_booking_num(cxn, booking_num) is False:
            print("Error: Could not validate booking number %s\n" % (booking_num))
            return -1
        # Otherwise, the booking exists for the user, and we can proceed
        # call DB procedure to update booking based on parameters
        if date is None:
            # we're only updating the timeslot, same date
            try:
                cur.callproc('update_booking', [booking_num, date, timeslot])
            except:
                print("Error updating. Please try again.\n")
                cxn.rollback()

            # we check affected row counts to make sure update worked
            if check_rows_affected(cur):
                # commit change
                cxn.commit()
                cur.close()
                return 0
            else:
                print("Error in updating the timeslot.\n")
                return -1
        elif timeslot is None:
            # we're only updating the date, same timeslot
            try:
                cur.callproc('update_booking', [booking_num, date, timeslot])
            except:
                print("Error updating. Please try again.\n")
                cxn.rollback()
            
            if check_rows_affected(cur):
                # commit change
                cxn.commit()
                cur.close()
                return 0
            else:
                print("Error in updating the date.\n")
                return -1
        else:
            # we are updating both
            try:
                cur.callproc('update_booking', [booking_num, date, timeslot])
            except:
                print("Error updating. Please try again.\n")
                cxn.rollback()

            if check_rows_affected(cur):
                cxn.commit()
                cur.close()
                return 0
            else:
                print("Error in updating either time/date of booking.\n")
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1
    

# Returns a list of rooms that match a user's criteria (capacity, start time, date, projector, club association)
def find_rooms_with_criteria(cxn, args: list) -> list:
    returned_rows = []
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure to find_rooms_with_criteria
        cur.callproc('find_room_with_criteria', args)
        # For simplicity sake, we only return 10 rows, otherwise it clutters everything up
        returned_rows = cur.fetchmany(size=10)
        cur.close()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
    return returned_rows


# Creates a booking for the user
# Returns 0 on success, or -1 on error
def create_booking(cxn, args: list) -> int: 
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure create_booking
        try:
            cur.callproc('create_booking', args)
        except:
            print("Error in creating booking. Please try again.\n")
            cxn.rollback()

        if check_rows_affected(cur):
            # commit change
            cxn.commit()
            cur.close()
            return 0
        else:
            print("Error: Could not create booking.\n")
            return -1
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1


# Deletes a booking for a user, provided it exists
# Returns 0 on success, and -1 on error
def delete_booking(cxn, booking_num: int) -> int:
    try:
        # create cursor
        cur = cxn.cursor()
        # validate booking num first
        if validate_booking_num(cxn, booking_num) is False:
            return -1
        # call DB procedure delete_booking
        try:
            cur.callproc('delete_booking', [booking_num])
        except:
            print("Error in deleting booking. Please try again.\n")
            cxn.rollback()

        if check_rows_affected(cur):
            # commit change
            cxn.commit()
            cur.close()
            return 0
        else:
            print("Error: Could not delete booking.\n")
            return -1
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1


# Signs a user into one of their bookings, letting them also specify room condition
# Returns 0 on success, and -1 on error
def sign_into_booking(cxn, booking_num: int) -> int:
    try:
        # create cursor
        cur = cxn.cursor()
        # validate booking number first
        if validate_booking_num(cxn, booking_num) is False:
            return -1

        # call DB procedure check_into_room
        try:
            cur.callproc('check_into_room', [booking_num, nuid])
        except:
            print("Error signing into booking. Please try again.\n")
            cxn.rollback()

        if check_rows_affected(cur):
            # commit change
            cxn.commit()
            cur.close()
            return 0
        else:
            print("Error: You've already signed into this booking!\n")
            return -1
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return -1


# Sign out of the application (aka close DB connection)
def sign_out(cxn) -> None:
    cxn.close()


# Prints the menu of available choices to the user
def print_menu() -> None:
    print("1: View list of your current bookings\n")
    print("2: Update a booking\n")
    print("3: Create a booking\n")
    print("4: Delete a booking\n")
    print("5: Sign into a booking\n")
    print("6: Add club association\n")
    print("7: Sign out")

# Given a list of a user's bookings, prints them out for the user to see
def print_user_bookings(records: list) -> None:
    for row in records:
        date_string = row["date"].strftime('%m/%d/%Y')
        time_string = str(row["start_hour"]) + ':00'
        print('Booking ID:', str(row["booking_id"]), '\n', row["building_name"], 'Room', str(row["room_number"]), 'starting at', time_string, 'on', date_string, 'for club', str(row["organization_name"]))


# Given a list of available rooms, prints them out for the user
def print_available_rooms(records: list) -> None:
    for row in records:
        formatted_string = row["building"] + ' Room ' + str(row["room_number"]) + ', Capacity: ' + str(row["capacity"])
        print(formatted_string)

# Given a list of available time slots, prints them out for the user
def print_available_timeslots(records: list) -> None:
    for row in records:
        formatted_string = row["building_name"] + ' Room ' + str(row["room_number"]) + ' starting at ' + str(row["start_hour"]) + ':00'
        print(formatted_string)


# Main loop:
# Prompt connection to DB
username = input("Enter DB username: \n")
password = gp.getpass("Enter DB password: \n")

while(not_connected_to_db):
    try:
        cxn = pymysql.connect(host='localhost', 
                            user=username,
                            password=password,
                            database='final_project',
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)
        not_connected_to_db = False
        break
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        print("Credentials incorrect. Please try again.\n")
        username = input("Enter username for DB connection: \n")
        password = gp.getpass("Enter DB password: \n")
        continue


# Connect to DB
while(global_flag):
    while(not validated_flag):
        if counter >= 1:
            choice = input("Choose 2 to confirm NUID.\n")
        else:
        # prompt user to either a) register or b) sign in
            choice = input("Would you like to register an NUID (1), or sign in with an existing NUID (2)?\n")

        # register
        if choice == '1':
            user_nuid = input("Please enter your NUID:\n")
            user_name = input("Please enter your full name:\n")

            if create_user(cxn, int(user_nuid), user_name) == 0:
                print("User was successfully added.\n")
                cxn.close()

                # not connected to DB anymore
                not_connected_to_db = True
                # use old creds to re-open connection, hopefully will see new user
                try:
                    cxn = pymysql.connect(host='localhost', 
                        user=username,
                        password=password,
                        database='final_project',
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)
                    not_connected_to_db = True
                    counter += 1
                except pymysql.err.OperationalError as e:
                    print('Error: %d: %s' % (e.args[0], e.args[1]))
            else:
                print("Error: could not register.\n")
                exit(1)
        elif choice == '2':
            # sign in, prompt for NUID
            nuid = input("Please enter your NUID: \n")

            if validate_nuid(cxn, nuid) is False:
                print("Error: could not validate NUID %s.\n" % (nuid))
                exit(1)
            validated_flag = True
        print("Signed in successfully.\n")

    # Successfully validated with NUID, so we can print menu
    print("------------------------\n")
    print_menu()
    print("------------------------\n")
    menu_item = input("Select the number of the operation you want to do: \n")

    # View bookings
    if menu_item == '1':
        bookings = view_bookings(cxn)
        print("Your bookings: \n")
        print_user_bookings(bookings)

    # Update booking
    elif menu_item == '2':
        # Show user their bookings
        print("Your bookings: \n")
        bookings = view_bookings(cxn)

        if len(bookings) != 0:
            print_user_bookings(bookings)

            # Select booking number
            booking_num = input("Select booking number to update: \n")

            # show user available timeslots for that room
            if validate_booking_num(cxn, int(booking_num)) == 0:
                print("Error: Could not validate booking num.\n")
                break

            # call display_other_times
            other_available_slots = display_other_bookings(cxn, int(booking_num))
            print_available_timeslots(other_available_slots)

            # Get new day and time from user, could be None
            new_day = input("New day in YYYY-MM-DD format: \n")
            new_time = input("New start hour of booking, from 0 - 23: \n")

            # Update booking based on inputs
            if update_booking(cxn, int(booking_num), new_day, int(new_time)) == 0:
                print("Successfully updated booking %s.\n" % (booking_num))
            else:
                print("Error updating booking %s.\n" % (booking_num))
        else:
            print("You don't have any bookings yet!\n")

    # Create booking
    elif menu_item == '3':
        # Tell user what things they can select
        print("Please provide answers to the following booking criteria: room capacity, ADA compliancy, desired starting hour of reservation, desired date of reservation, projector, if this booking is associated with a club, and desired campus.\n")
        
        capacity = input("Capacity: \n")
        ada_compliant = input("Do you want an ADA compliant room? \n")
        start_hr = input("Starting hour, from 0-23: \n")
        day = input("Date, in YYYY-MM-DD format: \n")
        projector = input("Projector? \n")
        club_affiliation = input("Is this booking associated with a club? \n")
        campus = input("Campus of desired room:\n")

        # create list of arguments
        args = (int(capacity), yn_to_bool(ada_compliant), int(start_hr), day, yn_to_bool(projector), yn_to_bool(club_affiliation), campus)
        
        # find rooms that match entered criteria
        compatible_options = find_rooms_with_criteria(cxn, args)

        if len(compatible_options) != 0:
            # Show user available options
            print("Available options: \n")
            print_available_rooms(compatible_options)

            # Prompt user to select room number, building name, start hour and date
            print("Please provide the following criteria to create a booking based on the available options shown above: room number, building name, and club to associate with the booking\n")

            room_num = input("Room number: \n")
            building_name = input("Building name: \n")
            
            if yn_to_bool(club_affiliation) is True:
                club_name = input("Club name: \n")
            else:
                club_name = None

            # create list of args for create_booking DB procedure
            args_c = (int(nuid), int(room_num), building_name, int(start_hr), day, club_name)

            # actually create booking
            if create_booking(cxn, args_c) == 0:
                print("Successfully created booking!\n")
            else:
                print("Error in creating booking.\n")
        else:
            print("No results for entered criteria found.\n")

    # Delete booking
    elif menu_item == '4':
        # Show user their bookings
        bookings = view_bookings(cxn)

        if len(bookings) != 0:
            print("Your bookings: \n")
            print_user_bookings(bookings)

            # Ask user for booking num to delete
            b_num = input("Confirm booking number to delete: \n")

            # Actually delete booking
            if delete_booking(cxn, int(b_num)) == 0:
                print("Booking %s was successfully deleted!\n" % (b_num))
            else:
                print("Error in deleting booking %s.\n" % (b_num))
        else:
            print("You don't have any bookings yet!\n")

    # Sign into booking
    elif menu_item == '5':
        # Show user their bookings
        print("Your bookings: \n")
        bookings = view_bookings(cxn)

        if len(bookings) != 0:
            print_user_bookings(bookings)

            # Ask user for booking num
            b_num = input("Confirm booking number to check into: \n")

            # check into room
            if sign_into_booking(cxn, int(b_num)) == 0:
                print("Successfully signed into booking %s.\n" % (b_num))
            else:
                print("Error signing into booking %s.\n" % (b_num))
        else:
            print("You don't have any bookings yet!\n")

    # add club association to user
    elif menu_item == '6':
        # Ask user for club name
        club_name = input("Enter club name to add to user:\n")

        if add_club_officer(cxn, nuid, club_name) == 0:
            print("Successfully added club affiliation!\n")
        else:
            print("Error: Could not add club association.\n")
    # quit/sign out
    elif menu_item == '7':
        # close db connection
        sign_out(cxn)
        print("Signing out...\n")
        global_flag = False
    # default if wrong input
    else:
        print("Invalid operation number, please re-enter.\n")
    