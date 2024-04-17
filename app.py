#!usr/bin/env python
import pymysql

# TODO: Ask for user to re-enter credentials if they mess up
# TODO: Clean up code style
# TODO: Error handling from MySQL procedures (or more informative error handling)
# TODO: Input sanitization/validation for various instances of user input!
# TODO: Figure out what to do if student doesn't exist in DB
# TODO: Figure out how to reprompt user for invalid inputs/we just error and return to main menu

# variables for state management
nuid = -1
global_flag = True
connected_to_db = False

# CRUD functions, and various other helper functions

# Initialize a database connection
def initialize_db_connection(username: str, password: str) -> any:
    try:
        cxn = pymysql.connect(host='localhost', 
                            user=username,
                            password=password,
                            database='final_project',
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)
        print('Successfully connected to MySQL!\n')
        return cxn
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))
        return None

# Utility function to check that an UPDATE, INSERT or DELETE operation was successful
# Returns True if the procedure update the rows needed, False otherwise
def check_rows_affected(cur) -> bool:
    affected_rows = cur.rowcount
    return affected_rows > 0


# Convert yes/no responses to boolean values
def yn_to_bool(choice: str) -> bool:
    return choice.lower() == 'yes'


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
    validated_rows = []
    try:
        # create cursor
        cur = cxn.cursor()
        # call DB procedure to check if booking num in user's list of bookings
        cur.callproc('validate_booking_num', [booking_num, nuid])
        validated_rows = cur.fetchall()
        cur.close()
    except pymysql.err.OperationalError as e:
        print('Error: %d: %s' % (e.args[0], e.args[1]))

    # If we return no rows, exit the function and we'll handle the error in the main app loop
    return len(validated_rows) > 0
    

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
            cur.callproc('update_booking', [timeslot])

            # we check affected row counts to make sure update worked
            if check_rows_affected(cur):
                cur.close()
                return 0
            else:
                print("Error in updating the timeslot.\n")
                return -1
        elif timeslot is None:
            # we're only updating the date, same timeslot
            cur.callproc('update_booking', [date])
            
            if check_rows_affected(cur):
                cur.close()
                return 0
            else:
                print("Error in updating the date.\n")
                return -1
        else:
            # we are updating both
            cur.callproc('update_booking', [timeslot, date])

            if check_rows_affected(cur):
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
        returned_rows = cur.fetchall()
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
        cur.callproc('create_booking', args)

        if check_rows_affected(cur):
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
        cur.callproc('delete_booking', [booking_num])

        if check_rows_affected(cur):
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
        cur.callproc('check_into_room', [booking_num])

        if check_rows_affected(cur):
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
    print("6: Sign out")

# Given a list of bookings, prints them out for the user to see
def print_bookings(records: list) -> None:
    for row in records:
        print(row)


# Control flow of main loop:
# Connect to DB
# Ask user for NUID -> validate with function -> quit and close on error? or re-prompt like, twice and then exit idk
# Once NUID validated: print menu
# User selects a choice, switch statement i guess
# Once operation finished, return to menu
# If user selects sign out -> close DB connection

while(not connected_to_db):
    # Prompt connection to DB
    username = input("Enter DB username: \n")
    password = input("Enter DB password: \n")
    
    cxn = initialize_db_connection(username, password)

    if cxn is None:
        print("Could not connect, please re-enter your credentials.\n")
    else:
        connected_to_db = True
        break

# Connect to DB
while(global_flag):
    # prompt for NUID
    nuid = input("Please enter your NUID: \n")

    if validate_nuid(cxn, nuid) is False:
        print("Error: could not validate NUID %s.\n" % (nuid))
        exit(1)
    
    # Successfully validated with NUID, so we can print menu
    print_menu()
    menu_item = input("Select the number of the operation you want to do: \n")

    # View bookings
    if menu_item == '1':
        bookings = view_bookings(cxn)
        print_bookings(bookings)
    # Update booking
    elif menu_item == '2':
        # Show user their bookings
        print("Your bookings: \n")
        bookings = view_bookings(cxn)
        print_bookings(bookings)

        # Select booking number
        booking_num = input("Select booking number to update: \n")

        # Get new day and time from user, could be None
        new_day = input("New day in YYYY-MM-DD format: \n")
        new_time = input("New start hour of booking, from 0 - 23: \n")

        # Update booking based on inputs
        if update_booking(cxn, int(booking_num), new_day, int(new_time)) == 0:
            print("Successfully updated booking %s.\n" % (booking_num))
        else:
            print("Error updating booking %s.\n" % (booking_num))
    # Create booking
    elif menu_item == '3':
        # Tell user what things they can select
        print("Please provide answers to the following booking criteria: room capacity, ADA compliancy, desired starting hour of reservation, desired date of reservation, projector, and if this booking is associated with a club\n")
        
        capacity = input("Capacity: \n")
        ada_compliant = input("Do you want an ADA compliant room? \n")
        start_hr = input("Starting hour, from 0-23: \n")
        day = input("Date, in YYYY-MM-DD format: \n")
        projector = input("Projector? \n")
        club_affiliation = input("Is this booking associated with a club? \n")

        # create list of arguments, with NUID as the first
        args = [int(nuid), int(capacity), yn_to_bool(ada_compliant), int(start_hr), day, yn_to_bool(projector), yn_to_bool(club_affiliation)]
        
        # find rooms that match entered criteria
        compatible_options = find_rooms_with_criteria(cxn, args)

        # Show user available options
        print("Available options: \n")
        print_bookings(compatible_options)

        # Prompt user to select room number, building name, start hour and date
        print("Please provide the following criteria to create a booking based on the available options shown above: room number, building name, and club to associate with the booking\n")

        room_num = input("Room number: \n")
        building_name = input("Building name: \n")
        club_name = input("Club name: \n")

        # create list of args for create_booking DB procedure
        args_c = [int(nuid), int(room_num), building_name, int(start_hr), day, club_name]

        # actually create booking
        if create_booking(cxn, args_c) == 0:
            print("Successfully created booking!\n")
        else:
            print("Error in creating booking.\n")
    # Delete booking
    elif menu_item == '4':
        # Show user their bookings
        print("Your bookings: \n")
        bookings = view_bookings(cxn)
        print_bookings(bookings)

        # Ask user for booking num to delete
        b_num = input("Confirm booking number to delete: \n")

        # Actually delete booking
        if delete_booking(cxn, int(b_num)) == 0:
            print("Booking %s was successfully deleted!\n" % (b_num))
        else:
            print("Error in deleting booking %s.\n" % (b_num))
    # Sign into booking
    elif menu_item == '5':
        # Show user their bookings
        print("Your bookings: \n")
        bookings = view_bookings(cxn)
        print_bookings(bookings)

        # Ask user for booking num
        b_num = input("Confirm booking number to check into: \n")

        # check into room
        if sign_into_booking(cxn, int(b_num)) == 0:
            print("Successfully signed into booking %s.\n" % (b_num))
        else:
            print("Error signing into booking %s.\n" % (b_num))

    # quit/sign out
    elif menu_item == '6':
        # close db connection
        sign_out()
        global_flag = False
    # default if wrong input?
    else:
        print("Invalid operation number, please re-enter.\n")
    