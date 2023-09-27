from datetime import datetime, timedelta, time, timezone
from calendarweek import CalendarWeek
from bs4 import BeautifulSoup 
import requests
import uuid 
import sys

current_cw = CalendarWeek().week
url = f"http://splan.hs-el.de/index.php?modus=1&kw={current_cw}&kwstart={current_cw}&fb=2&print=0&id=E057A1&infos=0&mo=1&di=1&mi=1&do=1&fr=1&sa=1&so=1&showkw=0"

def fetch():
    response = requests.get(url)

    if(response.status_code != 200):
        print(f"HTTP request failed with error code {response.status_code}")
        log_error(f"HTTP request failed with error code {response.status_code}")
        sys.exit(1)
    else:
        return response.text

def build_event_collection(html):

    event_collection = []

    page_soup = BeautifulSoup(html, "html.parser")
    event_table = page_soup.find_all("table", class_="planalle")[0]
    table_rows = event_table.find_all("tr")

    # Main loop to extract event information
    for table_row_index in range(len(table_rows)):

        weekdayindex = 0 # Monday

        for table_row_cell in table_rows[table_row_index]:
            if("plannewday" in table_row_cell["class"]):
                weekdayindex += 1
            if("plansched" in table_row_cell["class"]):

                event_collection.append({
                    "name": str(table_row_cell.find("b")).replace("<br/>", " ").replace("<b>", " ",).replace("</b>", " ").strip(),
                    "start_time": build_iso_datetime(calculate_date(weekdayindex), calculate_time(table_row_index)),
                    "end_time": build_iso_datetime(calculate_date(weekdayindex), calculate_time(table_row_index + int(table_row_cell.get("rowspan")))),
                    "duration": calculate_duration(table_row_cell.get("rowspan")),
                    "location": table_row_cell.find("a").text,
                    "professor": str(table_row_cell).split("<br/><br/>")[1].split("<br/>")[0].strip(),
                    "link": table_row_cell.find("a").get("href")
                })

    return event_collection

def calculate_duration(sum_quarters):
    return int(sum_quarters) * 15

def calculate_time(row_index):
    initial_time = time(hour=8, minute=0)
    current_datetime = datetime.combine(datetime.today(), initial_time)
    minutes_to_add = int(row_index) * 15
    return (current_datetime + timedelta(minutes=minutes_to_add)).time()

def calculate_date(weekdayindex):
    current_week = CalendarWeek()
    return current_week[weekdayindex - 1]

def build_iso_datetime(date, time):
    date_list = str(date).split('-')
    time_list = str(time).split(':')

    return datetime(int(date_list[0]), 
                    int(date_list[1]), 
                    int(date_list[2]), 
                    int(time_list[0]), 
                    int(time_list[1]), 
                    int(time_list[2])).strftime("%Y%m%dT%H%M%S") # Replace 'Z' so that not timezone is applied

def build_week_calendar(event_collection):

    ics_content = f"BEGIN:VCALENDAR\n"
    ics_content += f"VERSION:2.0\n"
    ics_content += f"PRODID: HS Student\n"

    for event in event_collection:
        ics_content += f"BEGIN:VEVENT\n"
        ics_content += f"UID:{generate_unique_uid()}\n"
        ics_content += f"DTSTART:{event['start_time']}\n"
        ics_content += f"DTEND:{event['end_time']}\n"
        ics_content += f"SUMMARY:{event['name']}\n"
        ics_content += f"LOCATION:{event['professor']} - {event['location']}\n"
        ics_content += f"URL:{event['link']}\n"
        ics_content += f"END:VEVENT\n"
    
    ics_content += f"END:VCALENDAR\n"

    write_week_calendar_to_file(ics_content)    

def write_week_calendar_to_file(calendar):
    with open(f"CW_{current_cw}.ics", "w") as f:
        f.writelines(calendar)
    print(f"CW_{current_cw} has been successfully created")
    log_success()

def log_success():
    with open("calendarparser.log", "a") as f:
        f.writelines("\n" + str(datetime.now().date()) + " " + str(datetime.now().time()).split('.')[0])
        f.writelines(f' | Successfully created file CW_{current_cw}.ics\n')
        f.writelines('----------------------------------------------------------------')

def log_error(message):
    with open("calendarparser.log", "a") as f:
        f.writelines("\n" + str(datetime.now().date()) + " " + str(datetime.now().time()).split('.')[0])
        f.writelines(f' | ERROR creating file CW_{current_cw}.ics\n\n')
        f.writelines(message + "\n\n")
        f.writelines('----------------------------------------------------------------')

def generate_unique_uid():
    unique_id = uuid.uuid4()
    timestamp = datetime.now().timestamp()
    return f"{unique_id}-{int(timestamp)}"


def main():
    reponse_html = fetch()
    event_collection = build_event_collection(reponse_html)
    build_week_calendar(event_collection)

if __name__ == "__main__":
    main()