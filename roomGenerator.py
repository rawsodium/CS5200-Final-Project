import csv
import random
# Generate a csv file for import into a MYSQL database of rooms inside on a campus
# A list of buildings, and their number of floors is provided
# The csv file will have the following columns:
    # room_number int,
    # capacity int,
    # ada boolean,
    # projector boolean,
    # club_only boolean,
    # building  VARCHAR(64),
    # FOREIGN KEY (building) REFERENCES buildings(name),
    # PRIMARY KEY (room_number, building)

buildings = [
    ["Richards Hall", 4],
    ["Ell Hall", 4],
    ["Hayden Hall", 4],
    ["Churchill Hall", 5],
    ["Forsyth Hall", 2],
    ["Snell Engineering", 4],
    ["Snell Library", 4],
    ["Shillman Hall", 4],
    ["West Village H", 17],
    ["West Village G", 7],
    ["Mills Hall", 4],
    ["Rothwell Center", 2],
    ["Stern Hall", 4],
    ["Carnegie Hall", 3],
    ["F.W. Olin Library", 4],
    ["Lisser Hall", 4],
    ["Lokey School", 3],
    ["Sage Hall", 2],
    ["Cowell", 2],
    ["Moore Natural Sciences Building", 4],
    ["Roux Institute", 5],
    ["First Canadian Place", 12],
    ["Devon House", 6]
]

# create the csv file
with open('rooms.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["room_number", "capacity", "ada", "projector", "club_only", "building"])
    # For each building, generate rooms for each floor
    for building in buildings:
        for floor in range(1, building[1] + 1):
            # For each room, generate random values for capacity, ada, projector, and club_only
            for room in range(1, 10):
                capacity = random.randint(10, 100)
                ada = random.choice([True, False])
                projector = random.choice([True, False])
                club_only = random.choice([True, False])
                writer.writerow([room + floor * 100, capacity, ada, projector, club_only, building[0]])
                # print([room + floor * 100, capacity, ada, projector, club_only, building[0]])

# Create a csv file for room timeslots
# a room timeslot will have the following columns:
# 	room_number int,
#     building_name  VARCHAR(64),
#     start_hour int,

# read the rooms.csv file and generate timeslots for each room
with open('rooms.csv', mode='r') as file:
    reader = csv.reader(file)
    next(reader) # skip the header
    with open('timeslots.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["room_number", "building_name", "start_hour"])
        for row in reader:
            # generate a random range of timeslots for each room
            firstSlot = random.randint(8, 12)
            lastSlot = random.randint(16, 21)
            for hour in range(firstSlot, lastSlot):
                writer.writerow([row[0], row[5], hour])