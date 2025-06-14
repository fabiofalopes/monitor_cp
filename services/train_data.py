import threading
import time
import requests
from typing import Dict, List, Optional, Any
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class TrainDataService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.trains_data = {}
        self.stations_data = {}
        self.station_index = {}
        self.all_stations_coords = {}
        self.cached_train_details = {}  # Cache train details to avoid repeated API calls
        self.last_station_fetch = 0
        
        # Expanded list of major stations for better coverage
        self.major_stations = [
            "94-31039",  # Lisboa Oriente
            "94-2006",   # Porto Campanha
            "94-73007",  # Faro
            "94-36004",  # Coimbra-B
            "94-30007",  # Lisboa Santa Apolonia
            "94-1008",   # Porto São Bento
            "94-29157",  # Braga
            "94-83006",  # Évora
        ]
        
        # Pre-load more station coordinates for better map coverage
        self.station_coords = {
            "94-31039": [-9.0978, 38.7681],  # Lisboa Oriente
            "94-2006": [-8.5856, 41.1496],   # Porto Campanha
            "94-73007": [-7.9304, 37.0194],  # Faro
            "94-36004": [-8.4103, 40.2033],  # Coimbra-B
            "94-30007": [-9.1255, 38.7223],  # Lisboa Santa Apolonia
            "94-1008": [-8.6109, 41.1456],   # Porto São Bento
            "94-29157": [-8.4347, 41.5479],  # Braga
            "94-83006": [-7.9067, 38.5667],  # Évora
        }
        
    def start(self):
        """Start the background data fetching service."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._fetch_loop, daemon=True)
            self.thread.start()
            logger.info("Train data service started")
            
    def stop(self):
        """Stop the background data fetching service."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Train data service stopped")
        
    def _fetch_loop(self):
        """Main loop for fetching train data."""
        # Load station index in background
        station_thread = threading.Thread(target=self._load_station_index, daemon=True)
        station_thread.start()
        
        # Start fetching trains immediately
        while self.running:
            try:
                self._fetch_all_trains_parallel()
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Error in train data fetch loop: {e}")
                time.sleep(30)  # Wait longer on error
                
    def _load_station_index(self):
        """Load the station index from CP API."""
        try:
            response = requests.get("https://www.cp.pt/sites/spring/station-index", timeout=15)
            response.raise_for_status()
            self.station_index = response.json()
            logger.info(f"Loaded {len(self.station_index)} stations")
            
            # Try to fetch coordinates for more stations from the API
            self._fetch_additional_station_coords()
            
        except Exception as e:
            logger.error(f"Failed to load station index: {e}")
            
    def _fetch_additional_station_coords(self):
        """Try to fetch coordinates for additional stations."""
        # This would require additional API exploration or external data sources
        # For now, we'll use our predefined coordinates
        pass
            
    def _fetch_all_trains_parallel(self):
        """Fetch trains from all major stations using parallel requests for better performance."""
        new_trains_data = {}
        
        # Use ThreadPoolExecutor for parallel station queries
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all station queries in parallel
            station_futures = {
                executor.submit(self._fetch_trains_at_station, station_id): station_id 
                for station_id in self.major_stations
            }
            
            # Collect all trains from all stations
            all_trains = []
            for future in as_completed(station_futures):
                station_id = station_futures[future]
                try:
                    trains_at_station = future.result()
                    for train in trains_at_station:
                        train['source_station'] = station_id  # Track where we found this train
                        all_trains.append(train)
                except Exception as e:
                    logger.error(f"Error fetching trains for station {station_id}: {e}")
            
            # Now fetch train details in parallel (with caching)
            unique_trains = {}
            for train in all_trains:
                train_id = str(train.get('trainNumber'))
                if train_id and train_id not in unique_trains:
                    unique_trains[train_id] = train
            
            # Parallel train detail fetching
            detail_futures = {
                executor.submit(self._fetch_train_details_cached, train_id): (train_id, train_data)
                for train_id, train_data in unique_trains.items()
            }
            
            for future in as_completed(detail_futures):
                train_id, train_basic = detail_futures[future]
                try:
                    train_details = future.result()
                    if train_details and self._has_valid_coordinates(train_details):
                        processed_train = self._process_train_data(train_basic, train_details)
                        new_trains_data[train_id] = processed_train
                except Exception as e:
                    logger.error(f"Error processing train {train_id}: {e}")
                
        self.trains_data = new_trains_data
        logger.info(f"Updated data for {len(self.trains_data)} trains")
        
    def _fetch_trains_at_station(self, station_id: str) -> List[Dict]:
        """Fetch trains at a specific station."""
        try:
            url = f"https://www.cp.pt/sites/spring/station/trains?stationId={station_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch trains for station {station_id}: {e}")
            return []
            
    def _fetch_train_details_cached(self, train_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific train with caching."""
        # Check cache first (cache for 5 minutes)
        cache_key = train_id
        current_time = time.time()
        
        if cache_key in self.cached_train_details:
            cached_data, cache_time = self.cached_train_details[cache_key]
            if current_time - cache_time < 300:  # 5 minutes cache
                return cached_data
        
        # Fetch fresh data
        try:
            url = f"https://www.cp.pt/sites/spring/station/trains/train?trainId={train_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self.cached_train_details[cache_key] = (data, current_time)
            
            # Clean old cache entries (keep cache size manageable)
            if len(self.cached_train_details) > 1000:
                old_keys = [k for k, (_, t) in self.cached_train_details.items() 
                           if current_time - t > 600]  # Remove entries older than 10 minutes
                for k in old_keys:
                    del self.cached_train_details[k]
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch details for train {train_id}: {e}")
            return None
            
    def _has_valid_coordinates(self, train_details: Dict) -> bool:
        """Check if train has valid GPS coordinates."""
        lat = train_details.get('latitude')
        lng = train_details.get('longitude')
        
        if not lat or not lng:
            return False
            
        try:
            lat_float = float(lat)
            lng_float = float(lng)
            
            # Check if coordinates are within Portugal bounds (approximately)
            return (36.0 <= lat_float <= 42.5) and (-10.0 <= lng_float <= -6.0)
        except (ValueError, TypeError):
            return False
            
    def _process_train_data(self, train_basic: Dict, train_details: Dict) -> Dict:
        """Process and combine train data for map display."""
        service_info = train_basic.get('trainService', {})
        
        # Extract more detailed information
        train_stops = train_details.get('trainStops', [])
        
        return {
            'trainId': str(train_basic.get('trainNumber')),
            'trainNumber': train_basic.get('trainNumber'),
            'serviceCode': service_info.get('code', 'T'),
            'serviceName': service_info.get('designation', 'Train'),
            'lat': float(train_details.get('latitude')),
            'lng': float(train_details.get('longitude')),
            'status': train_details.get('status', 'UNKNOWN'),
            'delay': train_basic.get('delay', 0) or 0,
            'origin': train_basic.get('trainOrigin', {}).get('designation', 'Unknown'),
            'destination': train_basic.get('trainDestination', {}).get('designation', 'Unknown'),
            'platform': train_basic.get('platform'),
            'occupancy': train_basic.get('occupancy') or train_details.get('occupancy'),
            'eta': train_basic.get('eta'),
            'etd': train_basic.get('etd'),
            'arrivalTime': train_basic.get('arrivalTime'),
            'departureTime': train_basic.get('departureTime'),
            'route': self._extract_route_coordinates(train_details),
            'trainStops': train_stops,
            'sourceStation': train_basic.get('source_station'),
            'lastUpdate': time.time(),
            'fullDetails': train_details  # Store full details for popup display
        }
        
    def _extract_route_coordinates(self, train_details: Dict) -> List[List[float]]:
        """Extract route coordinates from train stops."""
        coordinates = []
        train_stops = train_details.get('trainStops', [])
        
        for stop in train_stops:
            lat = stop.get('latitude')
            lng = stop.get('longitude')
            
            if lat and lng:
                try:
                    coordinates.append([float(lng), float(lat)])
                except (ValueError, TypeError):
                    continue
                    
        return coordinates
        
    def get_all_trains(self) -> Dict[str, Dict]:
        """Get all current train data."""
        return self.trains_data.copy()
        
    def get_train_details(self, train_id: str) -> Optional[Dict]:
        """Get detailed information for a specific train."""
        train = self.trains_data.get(train_id)
        if train:
            return train
        return None
        
    def get_train_route(self, train_id: str) -> List[List[float]]:
        """Get route coordinates for a specific train."""
        train = self.trains_data.get(train_id)
        if train:
            return train.get('route', [])
        return []
        
    def get_all_stations(self) -> List[Dict]:
        """Get information about all available stations for map display."""
        if not self.station_index:
            return []
            
        stations = []
        
        # Add major stations first (with coordinates)
        major_station_names = set()
        for station_id in self.major_stations:
            station_name = None
            for name, id_val in self.station_index.items():
                if id_val == station_id:
                    station_name = name.title()
                    break
                    
            if station_name:
                coords = self._get_station_coordinates(station_id)
                if coords:
                    trains_at_station = self._get_trains_at_station_from_data(station_id)
                    stations.append({
                        'stationId': station_id,
                        'name': station_name,
                        'lat': coords[1],
                        'lng': coords[0],
                        'type': 'major',
                        'hasTrains': len(trains_at_station) > 0,
                        'trains': trains_at_station
                    })
                    major_station_names.add(station_name.lower())
        
        # Add other stations from train stops (discovered through train data)
        discovered_stations = set()
        station_train_map = {}
        
        # First pass: collect all stations and their trains
        for train in self.trains_data.values():
            for stop in train.get('trainStops', []):
                station_name = stop.get('station', {}).get('designation') or stop.get('designation')
                lat = stop.get('latitude')
                lng = stop.get('longitude')
                
                if station_name and lat and lng and station_name not in discovered_stations:
                    try:
                        lat_float = float(lat)
                        lng_float = float(lng)
                        if (36.0 <= lat_float <= 42.5) and (-10.0 <= lng_float <= -6.0):
                            # Check if this is not already a major station
                            is_major = any(station_name.lower() in major_name or major_name in station_name.lower() 
                                         for major_name in major_station_names)
                            
                            if not is_major:
                                if station_name not in station_train_map:
                                    station_train_map[station_name] = {
                                        'lat': lat_float,
                                        'lng': lng_float,
                                        'trains': []
                                    }
                                
                                # Add train info
                                station_train_map[station_name]['trains'].append({
                                    'trainId': train['trainId'],
                                    'trainNumber': train['trainNumber'],
                                    'serviceCode': train['serviceCode'],
                                    'destination': train['destination'],
                                    'delay': train['delay']
                                })
                                
                                discovered_stations.add(station_name)
                    except (ValueError, TypeError):
                        continue
        
        # Add discovered stations
        for station_name, station_info in station_train_map.items():
            stations.append({
                'stationId': f"discovered_{station_name.replace(' ', '_')}",
                'name': station_name.title(),
                'lat': station_info['lat'],
                'lng': station_info['lng'],
                'type': 'regular',
                'hasTrains': len(station_info['trains']) > 0,
                'trains': station_info['trains'][:5]  # Limit to 5 trains for performance
            })
                        
        return stations
        
    def _get_trains_at_station_from_data(self, station_id: str) -> List[Dict]:
        """Get trains currently at or passing through a station."""
        trains_at_station = []
        
        for train in self.trains_data.values():
            # Check if train originates from this station
            if train.get('sourceStation') == station_id:
                trains_at_station.append({
                    'trainId': train['trainId'],
                    'trainNumber': train['trainNumber'],
                    'serviceCode': train['serviceCode'],
                    'destination': train['destination'],
                    'delay': train['delay']
                })
            
            # Check if train stops at this station
            for stop in train.get('trainStops', []):
                station_code = stop.get('station', {}).get('code')
                if station_code == station_id:
                    trains_at_station.append({
                        'trainId': train['trainId'],
                        'trainNumber': train['trainNumber'],
                        'serviceCode': train['serviceCode'],
                        'destination': train['destination'],
                        'delay': train['delay']
                    })
                    break
        
        # Remove duplicates and limit
        seen = set()
        unique_trains = []
        for train in trains_at_station:
            if train['trainId'] not in seen:
                seen.add(train['trainId'])
                unique_trains.append(train)
                if len(unique_trains) >= 5:  # Limit for performance
                    break
        
        return unique_trains
        
    def get_major_stations(self) -> List[Dict]:
        """Get information about major stations for map display."""
        # Return empty list if station index not loaded yet
        if not self.station_index:
            return []
            
        stations = []
        
        for station_id in self.major_stations:
            # Find station name in the index
            station_name = None
            for name, id_val in self.station_index.items():
                if id_val == station_id:
                    station_name = name.title()
                    break
                    
            if station_name:
                # Get approximate coordinates for major Portuguese stations
                coords = self._get_station_coordinates(station_id)
                if coords:
                    stations.append({
                        'stationId': station_id,
                        'name': station_name,
                        'lat': coords[1],
                        'lng': coords[0],
                        'type': 'major',
                        'hasTrains': self._station_has_trains(station_id)
                    })
                    
        return stations
        
    def _station_has_trains(self, station_id: str) -> bool:
        """Check if a station currently has trains."""
        for train in self.trains_data.values():
            if train.get('sourceStation') == station_id:
                return True
            for stop in train.get('trainStops', []):
                if stop.get('stationId') == station_id:
                    return True
        return False
        
    def are_stations_ready(self) -> bool:
        """Check if station data is ready."""
        return bool(self.station_index)
        
    def _get_station_coordinates(self, station_id: str) -> Optional[List[float]]:
        """Get coordinates for stations, preferring API data over hardcoded coordinates."""
        # First try to get coordinates from API data (train stops)
        for train in self.trains_data.values():
            for stop in train.get('trainStops', []):
                station_code = stop.get('station', {}).get('code')
                if station_code == station_id:
                    lat = stop.get('latitude')
                    lng = stop.get('longitude')
                    if lat and lng:
                        try:
                            return [float(lng), float(lat)]
                        except (ValueError, TypeError):
                            continue
        
        # Fallback to hardcoded coordinates if API data not available
        return self.station_coords.get(station_id)
    
    def get_station_coordinates_by_id(self, station_id: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a station by ID, preferring API data."""
        # Use the updated _get_station_coordinates method which prioritizes API data
        coords = self._get_station_coordinates(station_id)
        if coords:
            return {'lng': coords[0], 'lat': coords[1]}
        
        return None
    
    def get_station_coordinates_by_name(self, station_name: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a station by name."""
        # First find the station ID from the name
        station_id = None
        for name, id_val in self.station_index.items():
            if name.lower() == station_name.lower():
                station_id = id_val
                break
        
        if station_id:
            return self.get_station_coordinates_by_id(station_id)
        
        # If not found in index, search through discovered stations
        for train in self.trains_data.values():
            for stop in train.get('trainStops', []):
                stop_name = stop.get('station', {}).get('designation') or stop.get('designation')
                if stop_name and stop_name.lower() == station_name.lower():
                    lat = stop.get('latitude')
                    lng = stop.get('longitude')
                    if lat and lng:
                        try:
                            return {'lng': float(lng), 'lat': float(lat)}
                        except (ValueError, TypeError):
                            continue
        
        return None

# Create a single instance of the service to be used by the app
train_service = TrainDataService() 