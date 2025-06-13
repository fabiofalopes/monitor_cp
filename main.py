"""
CP Train Data Viewer

A simple application to display train information from the CP API.
"""

import os
from typing import Dict, List, Any

import requests
from dotenv import load_dotenv
from nicegui import app, ui
from thefuzz import process

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
API_BASE_URL = "https://www.cp.pt/sites/spring"
STATION_INDEX_URL = f"{API_BASE_URL}/station-index"
TRAINS_URL = f"{API_BASE_URL}/station/trains"

DEFAULT_STATION_NAME = "Lisboa Oriente"
DEFAULT_STATION_ID = os.getenv("DEFAULT_STATION_ID", "94-31039")

# --- State Management ---
station_cache: Dict[str, str] = {}

# --- API Client ---
def get_station_index() -> Dict[str, str]:
    """Fetches the station index from the CP API."""
    try:
        response = requests.get(STATION_INDEX_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching station index: {e}")
        return {}

def get_trains_at_station(station_id: str) -> List[Dict[str, Any]]:
    """Fetches real-time train data for a given station."""
    try:
        params = {"stationId": station_id}
        response = requests.get(TRAINS_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching trains for station {station_id}: {e}")
        return []

def create():
    def handle_station_selection(station_name: str, station_id: str):
        """Callback function when a station is selected."""
        app.storage.user['selected_station_name'] = station_name
        app.storage.user['selected_station_id'] = station_id
        ui.navigate.to('/')

    @ui.page('/')
    def main_page():
        """Main UI page for the application."""
        selected_station_name = app.storage.user.get('selected_station_name', DEFAULT_STATION_NAME)
        
        # --- Header ---
        with ui.header(elevated=True).classes('items-center justify-between'):
            ui.label('Monitor CP').classes('text-lg sm:text-xl font-bold p-4')

            def handle_selection(e):
                if e.value and e.value in station_cache:
                    station_id = station_cache[e.value]
                    handle_station_selection(e.value, station_id)

            station_names = sorted(list(station_cache.keys()))
            ui.select(
                options=station_names, with_input=True, label='Search for a station...', on_change=handle_selection
            ).classes('w-64 sm:w-72 md:w-96 p-4').props('color=white dense outlined')

        # --- Filter Bar ---
        with ui.row().classes('w-full px-4 gap-4 items-center justify-center'):
            service_filter = ui.select(
                options=[], label="Filter by service", multiple=True, clearable=True
            ).classes('w-64').bind_value(app.storage.user, 'selected_services')
            
            train_number_filter = ui.input(
                label="Filter by train number",
            ).classes('w-48').props('clearable').bind_value(app.storage.user, 'search_train_number')

        # --- Scroll-to-Top FAB ---
        ui.button(icon='keyboard_arrow_up', on_click=lambda: ui.run_javascript("window.scrollTo({top: 0, behavior: 'smooth'})")) \
            .props('fab round color=accent') \
            .classes('fixed bottom-8 right-8 z-30')

        # --- Main Content ---
        with ui.column().classes('w-full p-4 items-center'):
            ui.label().classes('text-3xl font-bold mb-4').bind_text_from(
                app.storage.user, 'selected_station_name', lambda name: name or DEFAULT_STATION_NAME
            )
            live_board_container = ui.grid(
                columns=1,
            ).classes('w-full gap-4 sm:grid-cols-2 lg:grid-cols-3')

        def update_dashboard():
            """Fetches train data and dynamically builds the platform-centric live board."""
            station_id = app.storage.user.get('selected_station_id', DEFAULT_STATION_ID)
            all_trains = get_trains_at_station(station_id)

            # Update filter options based on all available trains
            if all_trains:
                all_services = sorted(list(set(t['trainService']['designation'] for t in all_trains)))
                service_filter.options = all_services
                service_filter.update()

            # Apply filters
            selected_services = app.storage.user.get('selected_services')
            search_train_number = app.storage.user.get('search_train_number')

            filtered_trains = all_trains
            if selected_services:
                filtered_trains = [t for t in filtered_trains if t['trainService']['designation'] in selected_services]
            if search_train_number:
                filtered_trains = [t for t in filtered_trains if search_train_number in str(t['trainNumber'])]
            
            live_board_container.clear()

            if not filtered_trains:
                with live_board_container:
                    ui.label("No matching train data found.").classes('text-center text-gray-500')
                return

            platforms = sorted(list(set(t['platform'] for t in filtered_trains if t.get('platform'))))
            trains_by_platform = {p: [t for t in filtered_trains if t.get('platform') == p] for p in platforms}

            with live_board_container:
                # --- Sticky Platform Navigation ---
                with ui.row().classes(
                    'w-full sticky top-0 bg-white/90 dark:bg-slate-900/90 '
                    'py-2 px-4 z-20 items-center shadow-md backdrop-blur-sm rounded-lg mb-4'
                ):
                    ui.label("Go to platform:").classes('flex-shrink-0 text-sm sm:text-base text-gray-600 dark:text-gray-300 font-medium mr-4')
                    
                    with ui.row().classes('flex-nowrap overflow-x-auto w-full gap-2'):
                        for platform in platforms:
                            js_command = f"document.getElementById('platform-{platform}').scrollIntoView({{ behavior: 'smooth' }});"
                            ui.button(platform, on_click=lambda cmd=js_command: ui.run_javascript(cmd)).props('flat dense')

                # --- Platform Sections ---
                with ui.grid().classes('w-full grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'):
                    for platform in platforms:
                        with ui.card().classes('w-full').props(f'flat bordered id=platform-{platform}'):
                            with ui.card_section().classes('bg-slate-100 dark:bg-slate-800'):
                                ui.label(f"Platform {platform}").classes('text-lg font-bold')
                            
                            with ui.card_section().classes('p-0'):
                                for train in sorted(trains_by_platform[platform], key=lambda t: t.get('etd') or t.get('eta') or '99:99'):
                                    with ui.row().classes('w-full items-center justify-between p-3 gap-4 border-b dark:border-gray-700'):
                                        # Part 1: Service Info
                                        with ui.row(wrap=False).classes('items-center gap-3 w-48'):
                                            service_code = train['trainService']['code']
                                            service_name = train['trainService']['designation']
                                            with ui.avatar(color='primary', text_color='white', size='md', square=True, rounded=True):
                                                ui.label(service_code).classes('text-sm font-bold')
                                            
                                            with ui.column().classes('gap-0'):
                                                ui.label(service_name).classes('font-semibold text-sm leading-tight')
                                                ui.label(f"#{train['trainNumber']}").classes('text-xs text-gray-500 dark:text-gray-400 leading-tight')

                                        # Part 2: Time, Delay, Occupancy (Now in the middle)
                                        with ui.row(wrap=False).classes('items-center gap-4'):
                                            with ui.column().classes('items-end gap-0'):
                                                # Prioritize estimated times, but fall back to scheduled times for display
                                                display_time = train.get('etd') or train.get('eta') or train.get('departureTime') or train.get('arrivalTime')
                                                
                                                scheduled_departure = train.get('departureTime')
                                                scheduled_arrival = train.get('arrivalTime')
                                                delay = train.get('delay') or 0

                                                if display_time:
                                                    ui.label(display_time).classes('font-bold text-xl')

                                                # Determine what to show as the secondary, smaller time
                                                secondary_display = None
                                                
                                                # If delayed, show the original scheduled time with a strikethrough
                                                if delay > 0:
                                                    original_time = scheduled_departure or scheduled_arrival
                                                    secondary_display = original_time
                                                
                                                # If it's a pass-through train, show the arrival/departure range
                                                elif scheduled_departure and scheduled_arrival and scheduled_departure != scheduled_arrival:
                                                    secondary_display = f"{scheduled_arrival} → {scheduled_departure}"

                                                if secondary_display:
                                                    classes = 'text-sm text-gray-500'
                                                    if delay > 0:
                                                        classes += ' line-through'
                                                    ui.label(secondary_display).classes(classes)

                                            with ui.column().classes('items-center w-20'):
                                                if delay > 0:
                                                    delay_color = 'red-600' if delay > 5 else 'orange-500'
                                                    ui.label(f"+{delay} min").classes(f"text-{delay_color} font-bold text-sm")
                                                else:
                                                    ui.label('On Time').classes('text-green-600 font-bold text-sm')

                                                occupancy = train.get('occupancy')
                                                if occupancy:
                                                    icon_map = {1: 'signal_cellular_1_bar', 2: 'signal_cellular_2_bar', 3: 'signal_cellular_3_bar'}
                                                    ui.icon(icon_map.get(occupancy, 'signal_cellular_off'), color='gray-500').classes('mt-1')

                                        # Part 3: Direction (Now on the right)
                                        with ui.column().classes('flex-grow items-end justify-center min-w-0'): # min-w-0 helps with flexbox truncation
                                            origin = train['trainOrigin']['designation']
                                            destination = train['trainDestination']['designation']
                                            with ui.row(wrap=False).classes('items-center justify-end w-full'):
                                                ui.label(origin).classes('text-sm text-gray-500 truncate')
                                                ui.icon('east', size='sm').classes('mx-2 text-gray-400')
                                                ui.label(destination).classes('font-bold text-md truncate')

        # When filters change, update the dashboard
        service_filter.on('update:model-value', update_dashboard)
        train_number_filter.on('update:model-value', update_dashboard)

        update_dashboard()
        ui.timer(30, update_dashboard)

    @app.on_startup
    async def on_startup():
        """Fetch station index on startup."""
        global station_cache
        print("Fetching station index...")
        station_cache = get_station_index()
        if station_cache:
            print(f"Successfully loaded {len(station_cache)} stations.")
        else:
            print("Failed to load station index. Search functionality will be unavailable.")

# --- UI Implementation ---
# This part is now inside create()

if __name__ in {"__main__", "__mp_main__"}:
    create()
    ui.run(storage_secret='a_random_and_long_secret_string_for_testing') 