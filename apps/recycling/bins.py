import requests
from datetime import datetime, timedelta
import json
import appdaemon.plugins.hass.hassapi as hass
import adbase as ad


class bins(hass.Hass):
    
    def create_bin_entity(self, date, recycleweek):
        self.my_entity = self.get_entity("sensor.recyclingbindate")
        currentdate = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        self.queuedlogger(currentdate)
        self.my_entity.set_state(state=recycleweek, attributes = {"last_update": currentdate, "red": True, "green": True, "yellow": recycleweek}, replace=True)

    def extract_recycling_items(self, api_url, start_date, end_date):
        self.queuedlogger("Started monitoring the bins")
        try:
            # Fetch data from the API
            response = requests.get(api_url, params={'start': start_date, 'end': end_date})
            response.raise_for_status()  # Raise an exception for bad responses

            # Parse the JSON response
            data = response.json()

            # Extract items with event_type equal to "recycling"
            recycling_items = [item for item in data if item.get('event_type', '').lower() == 'recycle']

            return recycling_items

        except requests.exceptions.RequestException as e:
            self.queuedlogger(f"Error fetching data: {e}")
            return None

    def update_bin_dates(self):
        binstartindex = 0
        default_start_date = datetime.now().date()
        default_end_date = (datetime.now() + timedelta(days=365)).date()
        api_url = f"https://wollongong.waste-info.com.au/api/v1/properties/70131.json"
        recycling_items = self.extract_recycling_items(api_url, default_start_date, default_end_date)     
        if recycling_items is not None:
            # get first entity start date, format and then check if in the next week. If not, return false, else true            
            date_format = '%Y-%m-%d'
            nextrecyclingdate = datetime.strptime(recycling_items[binstartindex].get('start'), date_format)
            todaysdate =  datetime.now()
            
            while (nextrecyclingdate < todaysdate):
                binstartindex += 1
                self.log(f"next recycling date is in the past, moving to next index {binstartindex}")
                nextrecyclingdate = datetime.strptime(recycling_items[binstartindex].get('start'), date_format)

            self.queuedlogger(f"Next recycling date is: {nextrecyclingdate.date()}")
            
            recycling_date_week = nextrecyclingdate.date().isocalendar()[1]
            self.queuedlogger(f"Next recycling week: {recycling_date_week}")

            curr_week = datetime.now().isocalendar()[1]
            self.queuedlogger(f"Current week: {curr_week}")
            # number of next week
            next_week = (datetime.now() + timedelta(weeks=1)).isocalendar()[1]
            self.queuedlogger(f"Next week: {next_week}")
            # number of the week after that
            week_after_next_week = (datetime.now() + timedelta(weeks=2)).isocalendar()[1]
            self.queuedlogger(f"Two weeks: {week_after_next_week}")

            if curr_week == recycling_date_week:
                self.queuedlogger("Recycling this week")
                self.create_bin_entity(nextrecyclingdate, True)
                pass
            else:
                self.queuedlogger("Recycling in the future")
                self.create_bin_entity(nextrecyclingdate, False)
                pass
            # self.log(recycling_items)

    def initialize(self):
        self.update_bin_dates()
        self.run_daily(self.run_daily_c, "01:13:00")

    def run_daily_c(self, cb_args):
        self.update_bin_dates()

    def queuedlogger(self, message):
        self.log(message) 
