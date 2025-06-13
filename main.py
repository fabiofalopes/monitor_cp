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

def capitalize_words(text: str) -> str:
    """Capitaliza cada palavra de uma string, tornando-a mais legível."""
    return ' '.join(word.capitalize() for word in text.split()) if text else ''

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

            # Capitalizar nomes das estações para a lista de seleção
            station_names = sorted(list(station_cache.keys()))
            station_options = [capitalize_words(name) for name in station_names]
            # Mapear nome capitalizado para o nome original para seleção correta
            station_name_map = {capitalize_words(name): name for name in station_names}
            def handle_selection_cap(e):
                if e.value and e.value in station_name_map:
                    station_id = station_cache[station_name_map[e.value]]
                    handle_station_selection(station_name_map[e.value], station_id)
            ui.select(
                options=station_options, with_input=True, label='Search for a station...', on_change=handle_selection_cap
            ).classes('w-64 sm:w-72 md:w-96 p-4').props('color=white dense outlined icon=search')

        # --- Main Content ---
        with ui.column().classes('w-full p-4 items-stretch gap-4'):
            # --- Control Deck ---
            with ui.card().classes('w-full'):
                with ui.card_section():
                    ui.label().classes('text-2xl font-bold').bind_text_from(
                        app.storage.user, 'selected_station_name', lambda name: capitalize_words(name or DEFAULT_STATION_NAME)
                    )
                
                ui.separator()

                with ui.card_section().classes('w-full'):
                    with ui.row().classes('w-full items-center gap-4'):
                        service_filter = ui.select(
                            options=[], label="Filter by service", multiple=True, clearable=True
                        ).classes('flex-grow').bind_value(app.storage.user, 'selected_services')
                        
                        train_number_filter = ui.input(
                            label="Filter by train number",
                        ).classes('flex-grow').props('clearable').bind_value(app.storage.user, 'search_train_number')

            # --- Live Board ---
            live_board_container = ui.column().classes('w-full gap-2')

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
                    ui.label("No matching train data found.").classes('text-center text-gray-500 p-4')
                return

            sorted_trains = sorted(filtered_trains, key=lambda t: t.get('etd') or t.get('eta') or t.get('departureTime') or t.get('arrivalTime') or '99:99')

            with live_board_container:
                with ui.list().classes('w-full'):
                    for train in sorted_trains:
                        with ui.item().classes('w-full p-0'):
                            with ui.row().classes('w-full items-center p-4 gap-x-4 gap-y-2 flex-wrap border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors'):
                                # Part 1: Service & Train Info
                                with ui.row(wrap=False).classes('items-center gap-4 w-52 min-w-[200px]'):
                                    service_code = train['trainService']['code']
                                    service_name = capitalize_words(train['trainService']['designation'])
                                    with ui.avatar(color='primary', text_color='white', size='lg', square=True, rounded=True):
                                        ui.label(service_code).classes('text-lg font-bold')
                                    
                                    with ui.column().classes('gap-0'):
                                        ui.label(service_name).classes('font-bold text-base leading-tight')
                                        ui.label(f"#{train['trainNumber']}").classes('text-sm text-gray-500 dark:text-gray-400 leading-tight')

                                # Part 2: Platform
                                with ui.row().classes('w-20 flex justify-center'):
                                    if train.get('platform'):
                                        with ui.card().classes('p-2 bg-sky-100 dark:bg-sky-900 rounded-lg'):
                                            ui.label(f"P {train['platform']}").classes('font-bold text-lg text-sky-800 dark:text-sky-200')

                                # Part 3: Time
                                with ui.column().classes('items-end gap-0 w-32 min-w-[120px]'):
                                    display_time = train.get('etd') or train.get('eta') or train.get('departureTime') or train.get('arrivalTime')
                                    scheduled_departure = train.get('departureTime')
                                    scheduled_arrival = train.get('arrivalTime')
                                    delay = train.get('delay') or 0

                                    if display_time:
                                        ui.label(display_time).classes('font-bold text-2xl')

                                    secondary_display = None
                                    if delay > 0:
                                        secondary_display = scheduled_departure or scheduled_arrival
                                    elif scheduled_departure and scheduled_arrival and scheduled_departure != scheduled_arrival:
                                        secondary_display = f"{scheduled_arrival} → {scheduled_departure}"
                                    
                                    if secondary_display:
                                        classes = 'text-sm text-gray-500'
                                        if delay > 0:
                                            classes += ' line-through'
                                        ui.label(secondary_display).classes(classes)
                                
                                # Part 4: Status
                                with ui.column().classes('items-start w-24 min-w-[80px]'):
                                    if delay > 0:
                                        delay_color = 'red-600' if delay > 5 else 'orange-500'
                                        ui.label(f"+{delay} min").classes(f"text-{delay_color} font-bold text-base")
                                    else:
                                        ui.label('On Time').classes('text-green-600 font-bold text-base')

                                # Part 5: Route
                                with ui.row(wrap=False).classes('items-center justify-end flex-grow min-w-0 gap-4 ml-auto'):
                                    with ui.column().classes('items-end gap-1 min-w-0'):
                                        origin = capitalize_words(train['trainOrigin']['designation'])
                                        destination = capitalize_words(train['trainDestination']['designation'])
                                        with ui.row(wrap=False).classes('items-center justify-end w-full'):
                                            ui.label(origin).classes('text-md text-gray-500 dark:text-gray-400 truncate')
                                            ui.icon('east', size='md').classes('mx-2 text-gray-400')
                                            ui.label(destination).classes('font-bold text-lg truncate')
        
        # --- Scroll-to-Top FAB ---
        ui.button(icon='keyboard_arrow_up', on_click=lambda: ui.run_javascript("window.scrollTo({top: 0, behavior: 'smooth'})")) \
            .props('fab round color=accent') \
            .classes('fixed bottom-8 right-8 z-30')

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