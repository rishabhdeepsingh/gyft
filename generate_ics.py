## Adds your timetable from `data.txt` to Google Calendar.
from __future__ import print_function
import os

import json
import datetime
import sys
import re
from icalendar import Calendar, Event

import dates
WORKING_DAYS = dates.get_dates()

import build_event

DEBUG = False
GENERATE_ICS = True
TIMETABLE_DICT_RE ='([0-9]{1,2}):([0-9]{1,2}):([AP])M-([0-9]{1,2}):([0-9]{1,2}):([AP])M'
timetable_dict_parser = re.compile(TIMETABLE_DICT_RE)

OUTPUT_FILENAME = "timetable.ics"

cal = Calendar()
cal.add('prodid', '-//Your Timetable generated by GYFT//mxm.dk//')
cal.add('version', '1.0')

'''
Given a starting timestamp d and a weekday number d (0-6), return the timestamp
of the next time this weekday is going to happen
'''
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def get_stamp(argument, date):
    '''
    argument is a 3-tuple such as
    ('10', '14', 'A') : 1014 HRS on date
    ('10', '4', 'P') : 2204 HRS on date
    '''

    hours_24_format = int(argument[0])

    # Note:
    # 12 PM is 1200 HRS
    # 12 AM is 0000 HRS

    if argument[2] == 'P' and hours_24_format != 12:
        hours_24_format = (hours_24_format + 12) % 24 

    if argument[2] == 'A' and hours_24_format == 12:
        hours_24_format = 0

    return build_event.generateIndiaTime(date.year,
            date.month,
            date.day,
            hours_24_format,
            int(argument[1]))

### days to number
days = {}
days["Monday"] = 0
days["Tuesday"] = 1
days["Wednesday"] = 2
days["Thursday"] = 3
days["Friday"] = 4
days["Saturday"] = 5
###

'''
Creates an ICS file `timetable.ics` with the timetable data present inside the
input file `data.txt`
'''
def main():

    # Get your timetable
    with open('data.txt') as data_file:    
        data = json.load(data_file)
    # Get subjects code and their respective name
    with open('subjects.json') as data_file:    
        subjects = json.load(data_file)
    for day in data:
        startDates = [next_weekday(x[0], days[day]) for x in WORKING_DAYS]

        for time in data[day]:
            # parsing time from time_table dict
            # currently we only parse the starting time
            # duration of the event is rounded off to the closest hour
            # i.e 17:00 - 17:55 will be shown as 17:00 - 18:00

            parse_results = timetable_dict_parser.findall(time)[0]

            lectureBeginsStamps = [get_stamp(parse_results[:3], start) \
                                                        for start in startDates]

            durationInHours = data[day][time][2]
            
            # Find the name of this course
            # Use subject name if available, else ask the user for the subject
            # name and use that
            # TODO: Add labs to `subjects.json`
            subject_code = data[day][time][0]
            summary = subject_code
            description = subject_code
            if (subject_code in subjects.keys()):
                summary = subjects[subject_code].title()
            else:
                print('ERROR: Our subjects database does not have %s in it.' %
                        subject_code);
                summary = input('INPUT: Please input the name of the course %s: ' %
                        subject_code)

                subjects[subject_code] = str(summary)

                summary = summary.title()

            # Find location of this class
            location = data[day][time][1]

            for lectureBegin, [periodBegin, periodEnd] in \
                    zip(lectureBeginsStamps, WORKING_DAYS):

                event = build_event.build_event_duration(summary,
                        description,
                        lectureBegin,
                        durationInHours,
                        location,
                        "weekly",
                        periodEnd)

                cal.add_component(event)

            if (DEBUG):
                print (event)

    with open(OUTPUT_FILENAME, 'wb') as f:
        f.write(cal.to_ical())
        print("INFO: Your timetable has been written to %s" % OUTPUT_FILENAME)

if __name__ == '__main__':
    main()
