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
from fastapi import FastAPI
from starlette.responses import Response

from components.map import Map
from services.train_data import train_service

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
API_BASE_URL = "https://www.cp.pt/sites/spring"
STATION_INDEX_URL = f"{API_BASE_URL}/station-index"
TRAINS_URL = f"{API_BASE_URL}/station/trains"

DEFAULT_STATION_NAME = "Lisboa Oriente"
DEFAULT_STATION_ID = os.getenv("DEFAULT_STATION_ID", "94-31039")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

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

    def create_header(show_search: bool = True):
        """Creates the header for all pages."""
        with ui.header(elevated=True).classes('items-center justify-between p-4'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center'):
                    ui.label('Monitor CP').classes('text-lg sm:text-xl font-bold')
                    ui.link('Station View', '/').classes('text-white mx-4')
                    
                    # Show current station in map link if one is selected
                    selected_station = app.storage.user.get('selected_station_name')
                    if selected_station:
                        map_link_text = f'Map View ({capitalize_words(selected_station)})'
                    else:
                        map_link_text = 'Map View'
                    ui.link(map_link_text, '/map').classes('text-white mx-4')

                if show_search:
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
                    ).classes('w-64 sm:w-72 md:w-96').props('color=white dense outlined icon=search')

    @ui.page('/')
    def main_page():
        """Main UI page for the application."""
        create_header()
        
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

    @ui.page('/map')
    def map_page():
        """Page to display the live train map."""
        create_header(show_search=False)

        if not MAPBOX_TOKEN:
            with ui.row().classes('w-full h-screen items-center justify-center'):
                ui.label('Mapbox token not found. Please set it in your .env file.').classes('text-red-500')
            return

        # Create a full-screen map container that accounts for the header
        # Use CSS calc to subtract header height from viewport height
        ui.add_head_html('''
        <style>
        .map-page-container {
            position: fixed;
            top: 64px; /* Header height */
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: calc(100vh - 64px);
        }
        </style>
        ''')
        
        with ui.element('div').classes('map-page-container'):
            map_view = Map(MAPBOX_TOKEN).classes('w-full h-full')

        # Center map around selected station if available
        def center_map_on_selected_station():
            """Center the map on the currently selected station."""
            selected_station_id = app.storage.user.get('selected_station_id')
            selected_station_name = app.storage.user.get('selected_station_name')
            
            coords = None
            if selected_station_id:
                # Try to get coordinates by station ID first
                coords = train_service.get_station_coordinates_by_id(selected_station_id)
                if not coords and selected_station_name:
                    # Fallback to station name lookup
                    coords = train_service.get_station_coordinates_by_name(selected_station_name)
            
            if coords:
                # Center map on the station with appropriate zoom level
                map_view.set_location(coords['lng'], coords['lat'], 12)
                print(f"Centered map on {selected_station_name or selected_station_id} at {coords['lng']}, {coords['lat']}")
            else:
                # Fallback to center on Portugal if no station selected or coordinates not found
                if selected_station_id or selected_station_name:
                    print(f"Could not find coordinates for station: {selected_station_name or selected_station_id}, using default Portugal view")
                else:
                    print("No station selected, showing default Portugal view")
                # Center on Portugal with a good overview zoom
                map_view.set_location(-8.61099, 39.69999, 7)

        # Add route request handler
        def handle_route_request(e):
            """Handle train route visualization requests from the map."""
            train_id = e.args[0] if e.args else None
            if train_id:
                route_coords = train_service.get_train_route(train_id)
                if route_coords:
                    map_view.draw_route(route_coords)
                
        # Connect the route request handler to the map
        map_view.on('request_train_route', handle_route_request)

        def update_map():
            """Fetches the latest train data and updates the map markers."""
            # Get all trains data
            trains = train_service.get_all_trains()
            trains_list = []
            
            for train in trains.values():
                trains_list.append({
                    'trainId': train['trainId'],
                    'trainNumber': train['trainNumber'],
                    'serviceCode': train['serviceCode'],
                    'serviceName': train['serviceName'],
                    'lng': train['lng'],
                    'lat': train['lat'],
                    'delay': train['delay'],
                    'origin': train['origin'],
                    'destination': train['destination'],
                    'status': train['status'],
                    'platform': train.get('platform'),
                    'occupancy': train.get('occupancy'),
                    'eta': train.get('eta'),
                    'etd': train.get('etd'),
                    'arrivalTime': train.get('arrivalTime'),
                    'departureTime': train.get('departureTime'),
                    'trainStops': train.get('trainStops', [])
                })
            
            # Update trains on map efficiently
            map_view.update_trains(trains_list)
            
            # Update all stations (including discovered ones from train data)
            if not hasattr(update_map, 'stations_updated') or len(trains_list) > 0:
                all_stations = train_service.get_all_stations()
                if all_stations:  # Only add if we have station data
                    if hasattr(update_map, 'stations_updated'):
                        # Update existing stations
                        map_view.update_all_stations(all_stations)
                    else:
                        # First time loading
                        map_view.add_stations_batch(all_stations)
                    update_map.stations_updated = True

        # Add initial stations and railway lines when service is ready
        def add_initial_data():
            """Add stations and railway lines as soon as the service has loaded them."""
            if not hasattr(add_initial_data, 'data_added'):
                # Start with major stations for immediate display
                major_stations = train_service.get_major_stations()
                if major_stations:
                    map_view.add_stations_batch(major_stations)
                    
                    # Also add railway lines in the background
                    try:
                        map_view.draw_railway_lines()
                        print("Railway lines loaded successfully")
                    except Exception as e:
                        print(f"Failed to load railway lines: {e}")
                    
                    add_initial_data.data_added = True
                    
                    # Center map on selected station after data is loaded
                    center_map_on_selected_station()
                    return True
            return False

        # Try to add data immediately, then in timer if not ready
        if not add_initial_data():
            # If data isn't ready, check every 2 seconds until it is
            def check_data():
                if add_initial_data():
                    return False  # Stop the timer
                return True  # Continue checking
            
            ui.timer(2, check_data)
        else:
            # If data was added immediately, try to center the map
            ui.timer(1, lambda: center_map_on_selected_station(), once=True)

        # Initial map update
        update_map()
        
        # Update the map every 15 seconds (reduced frequency for better performance)
        ui.timer(15, update_map)

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
        
        train_service.start()

    @app.on_shutdown
    def on_shutdown():
        """Stop background services."""
        train_service.stop()

# --- UI Implementation ---
# This part is now inside create()

if __name__ in {"__main__", "__mp_main__"}:
    create()
    ui.run(storage_secret='a_random_and_long_secret_string_for_testing') 