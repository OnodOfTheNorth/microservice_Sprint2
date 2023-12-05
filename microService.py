import datetime
import threading
import tkinter as tk
from tkinter import ttk, Label, Frame, Canvas, Scrollbar, VERTICAL, RIGHT, Y, W, E, N, S, Checkbutton
from PIL import Image, ImageTk
import os
import time

# Function to load the user's favorite teams from a file
def load_favorite_teams(filename):
    with open(filename, 'r') as file:
        favorite_teams = [line.strip() for line in file.readlines()]
    return favorite_teams

# Function to load events from a file
def load_events(filename):
    events = []
    with open(filename, 'r') as file:
        for line in file.readlines():
            parts = line.strip().split(',')
            if len(parts) == 4:
                events.append({
                    'team_name': parts[0],
                    'date': parts[1],
                    'time': parts[2],
                    'streaming_link': parts[3],
                })
    return events

# Function to filter events based on favorite teams and the current date
def filter_events(favorite_teams, events, range='today'):
    today = datetime.date.today()
    filtered_events = []
    if range == 'today':
        for event in events:
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event['team_name'] in favorite_teams and event_date == today:
                filtered_events.append(event)
    elif range == 'week':
        for event in events:
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event['team_name'] in favorite_teams and today <= event_date <= today + datetime.timedelta(days=7):
                filtered_events.append(event)
    elif range == 'month':
        for event in events:
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event['team_name'] in favorite_teams and today <= event_date <= today + datetime.timedelta(days=30):
                filtered_events.append(event)
    return filtered_events

# Function to update the user's favorite teams in a file
def update_favorite_teams(filename, teams):
    with open(filename, 'w') as file:
        for team in teams:
            file.write(team + '\n')

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Event Notifier")
        self.geometry('800x400')  # Adjust the window size
        self.configure(background='lightgray')
        
        # Create a tab control (notebook)
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both")
        
        # Variables to store favorites and events
        self.favorite_teams = []
        self.events = []
        self.filtered_events_today = []
        self.filtered_events_week = []
        self.filtered_events_month = []
        # Variables to check for file change
        self.last_modified_time = os.path.getmtime('favorites.txt')
        
        # Set up the UI
        self.setup_ui()
        
        # Start the file monitor thread
        self.start_file_monitor()

    def setup_ui(self):
        # Load the user's favorite teams from favorites.txt
        self.favorite_teams = load_favorite_teams('favorites.txt')
        # Create the second tab for favorite teams
        self.create_favorites_tab()

        # Load events from events.txt
        self.events = load_events('events.txt')
        # Filter the events for today
        self.filtered_events_today = filter_events(self.favorite_teams, self.events, range='today')
        # Filter the events for this week and month
        self.filtered_events_week = filter_events(self.favorite_teams, self.events, range='week')
        self.filtered_events_month = filter_events(self.favorite_teams, self.events, range='month')
        
        # Create the tabs for event notifications
        self.today_events_frame = self.create_events_tab("Today's Events", self.filtered_events_today)
        self.week_events_frame = self.create_events_tab("Week's Events", self.filtered_events_week)
        self.month_events_frame = self.create_events_tab("Month's Events", self.filtered_events_month)
        

    def create_events_tab(self, tab_name, events):
        events_frame = Frame(self.tab_control)
        self.tab_control.add(events_frame, text=tab_name)
        
        # Defer showing notifications until the UI is fully built
        # This also prevents issue when the frames are not ready yet
        self.after(100, lambda: self.show_notifications(events_frame, events, tab_name))
        
        return events_frame  # Return reference to the newly created frame


    def create_favorites_tab(self):
        self.favorites_frame = Frame(self.tab_control)
        self.tab_control.add(self.favorites_frame, text='Favorites')

        # Load all teams from file
        with open('teams.txt', 'r') as file:
            all_teams = [line.strip() for line in file.readlines()]

        # Dictionary to hold the team selections
        self.team_vars = {team: tk.BooleanVar(value=team in self.favorite_teams) for team in all_teams}

        def on_toggle():
            # Update the favorites based on Checkbutton selection
            self.favorite_teams = [team for team, var in self.team_vars.items() if var.get()]
            update_favorite_teams('favorites.txt', self.favorite_teams)

        for i, (team, var) in enumerate(self.team_vars.items()):
            check_button = Checkbutton(self.favorites_frame, text=team, variable=var, onvalue=True, offvalue=False, command=on_toggle)
            check_button.grid(row=i, column=0, sticky=W)

    def show_notifications(self, events_frame, filtered_events, tab_name):
        for widget in events_frame.winfo_children():
            widget.destroy()
        # Create a canvas and a scrollbar
        self.canvas = Canvas(events_frame, bg='lightgray')
        self.scrollbar = Scrollbar(events_frame, command=self.canvas.yview, orient=VERTICAL)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side='left', fill="both", expand=True)

        # Create a frame inside the canvas
        self.container_frame = Frame(self.canvas, bg='lightgray')
        self.canvas.create_window((0, 0), window=self.container_frame, anchor='nw')

        title_label = Label(self.container_frame, text=tab_name, font=('Arial', 16), bg='lightgray')
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 10), sticky=W+E)

        # Loop through the events, create individual frames for each event inside container_frame
        for i, event in enumerate(filtered_events):
            individual_event_frame = Frame(self.container_frame, bg='lightgray', bd=2)
            individual_event_frame.grid(row=i+1, column=0, sticky=W+E+N+S, padx=(50, 0), pady=(0, 10))

            logo_path = f"logos/{event['team_name'].replace(' ', '-')}.png"
            logo_image = Image.open(logo_path)

            # Resize the image while maintaining aspect ratio
            max_size = 100
            ratio = min(max_size / logo_image.width, max_size / logo_image.height)
            new_size = (int(logo_image.width * ratio), int(logo_image.height * ratio))
            logo_image = logo_image.resize(new_size, Image.BICUBIC)

            tk_image = ImageTk.PhotoImage(logo_image)

            label_image = Label(individual_event_frame, image=tk_image, bg='lightgray')
            label_image.image = tk_image  # Keep a reference
            label_image.grid(row=0, column=0)
            # Create a label to show the event info (team name, date(using strings instead of date format), time, and streaming link)
            event_info = f"{event['team_name']} on {event['date']} at {event['time']} on {event['streaming_link']}"
            label_info = Label(individual_event_frame, text=event_info, font=('Arial', 11), bg='lightgray', justify='left', anchor='w')
            label_info.grid(row=0, column=1, sticky=W)

        self.container_frame.update_idletasks()  # Update the inner frame's size
        self.canvas.config(scrollregion=self.canvas.bbox("all"))  # Set the scroll region of the canvas
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    def start_file_monitor(self):
        self.file_monitor_thread = threading.Thread(target=self.monitor_favorites_file, daemon=True)
        self.file_monitor_thread.start()

    def monitor_favorites_file(self):
        while True:
            current_modified_time = os.path.getmtime('favorites.txt')
            if self.last_modified_time != current_modified_time:
                self.last_modified_time = current_modified_time
                self.favorite_teams = load_favorite_teams('favorites.txt')
                self.filtered_events_today = filter_events(self.favorite_teams, self.events, range='today')
                self.filtered_events_week = filter_events(self.favorite_teams, self.events, range='week')
                self.filtered_events_month = filter_events(self.favorite_teams, self.events, range='month')
                self.update_ui()
            time.sleep(1)  # Check every second

    def update_ui(self):
        for team, var in self.team_vars.items():
            var.set(team in self.favorite_teams)

        # Update notifications
        for tab_name, events, filtered_events in [
            ("Today's Events", self.today_events_frame, self.filtered_events_today),
            ("Week's Events", self.week_events_frame, self.filtered_events_week),
            ("Month's Events", self.month_events_frame, self.filtered_events_month)
        ]:
            if tab_name == "Today's Events":
                self.show_notifications(self.today_events_frame, filtered_events, tab_name)
            elif tab_name == "Week's Events":
                self.show_notifications(self.week_events_frame, filtered_events, tab_name)
            elif tab_name == "Month's Events":
                self.show_notifications(self.month_events_frame, filtered_events, tab_name)

if __name__ == "__main__":
    app = Application()
    app.mainloop()