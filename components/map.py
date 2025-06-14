from nicegui import ui
import logging
from services.railway_lines import railway_service

class Map(ui.element, component='map.js', dependencies=['./map.js']):
    def __init__(self, token: str) -> None:
        super().__init__()
        ui.add_head_html('<link href="https://api.mapbox.com/mapbox-gl-js/v3.2.0/mapbox-gl.css" rel="stylesheet">')
        ui.add_head_html('<script src="https://api.mapbox.com/mapbox-gl-js/v3.2.0/mapbox-gl.js"></script>')
        
        # Add CSS for proper map sizing and optimized custom markers
        ui.add_head_html('''
        <style>
        .map-container {
            width: 100%;
            height: 100%;
            position: relative;
        }
        .map-element {
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 100%;
        }
        
        /* Optimized Train Marker Styles */
        .train-marker {
            cursor: pointer;
            transition: transform 0.15s ease-out;
            pointer-events: auto;
            z-index: 100; /* Lower base z-index than stations */
        }
        
        .train-marker:hover {
            transform: scale(1.05) translate(2px, -2px); /* Slight offset on hover */
            z-index: 150; /* Moderate z-index on hover */
        }
        
        .train-icon {
            background: white;
            border: 3px solid #3b82f6;
            border-radius: 8px;
            padding: 3px 6px;
            font-size: 10px;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
            min-width: 45px;
            white-space: nowrap;
            position: relative;
        }
        
        .train-icon.on-time {
            border-color: #10b981;
            background: #ecfdf5;
        }
        
        .train-icon.minor-delay {
            border-color: #f59e0b;
            background: #fffbeb;
        }
        
        .train-icon.delayed {
            border-color: #ef4444;
            background: #fef2f2;
        }
        
        .train-service {
            font-size: 11px;
            font-weight: bold;
            color: #1f2937;
            line-height: 1.1;
        }
        
        .train-number {
            font-size: 8px;
            color: #6b7280;
            line-height: 1;
            margin-top: 1px;
        }
        
        .delay-indicator {
            background: #ef4444;
            color: white;
            border-radius: 6px;
            padding: 1px 3px;
            font-size: 7px;
            font-weight: bold;
            line-height: 1;
            margin-top: 2px;
        }
        
        /* Optimized Station Marker Styles */
        .station-marker {
            cursor: pointer;
            transition: transform 0.15s ease-out;
            pointer-events: auto;
            z-index: 200; /* Higher base z-index than trains */
        }
        
        .station-marker:hover {
            transform: scale(1.15) translate(-2px, 2px); /* Larger scale and offset */
            z-index: 300; /* Higher z-index on hover */
        }
        
        .station-icon {
            background: white;
            border: 2px solid #6b7280;
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .station-icon-major {
            background: white;
            border: 3px solid #1d4ed8;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        }
        
        .station-icon-regular {
            background: white;
            border: 2px solid #9ca3af;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .station-icon.has-trains {
            border-color: #10b981;
            background: #ecfdf5;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 2px 8px rgba(0,0,0,0.2);
            animation: pulse-green 2s infinite;
        }
        
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 2px 8px rgba(0,0,0,0.2); }
            50% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.15), 0 4px 12px rgba(0,0,0,0.3); }
            100% { box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 2px 8px rgba(0,0,0,0.2); }
        }
        
        .station-icon.no-trains {
            border-color: #d1d5db;
            opacity: 0.7;
        }
        
        /* Ensure popups are always on top */
        .mapboxgl-popup {
            z-index: 10000 !important;
        }
        
        .mapboxgl-popup-content {
            max-height: 400px;
            overflow-y: auto;
            max-width: 350px;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            position: relative;
        }
        
        /* Hide close button since we removed it from popup configuration */
        .mapboxgl-popup-close-button {
            display: none !important;
        }
        
        /* Specific popup container styles */
        .train-popup-container .mapboxgl-popup-content {
            max-height: 450px;
        }
        
        .station-popup-container .mapboxgl-popup-content {
            max-height: 350px;
        }
        
        .railway-popup-container .mapboxgl-popup-content {
            max-height: 300px;
        }
        
        /* Custom scrollbar for popups */
        .mapboxgl-popup-content::-webkit-scrollbar {
            width: 6px;
        }
        
        .mapboxgl-popup-content::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        
        .mapboxgl-popup-content::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        .mapboxgl-popup-content::-webkit-scrollbar-thumb:hover {
            background: #a1a1a1;
        }
        
        /* Train stops section styling */
        .train-stops-section {
            margin-top: 12px;
            border-top: 1px solid #e5e7eb;
            padding-top: 12px;
        }
        
        .train-stops-section h4 {
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
            color: #374151;
        }
        
        .train-stops-list {
            max-height: 200px;
            overflow-y: auto;
        }
        
        .train-stop {
            padding: 6px 0;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .train-stop:last-child {
            border-bottom: none;
        }
        
        .train-stop.first-stop .stop-name {
            color: #059669;
            font-weight: 600;
        }
        
        .train-stop.last-stop .stop-name {
            color: #dc2626;
            font-weight: 600;
        }
        
        .stop-name {
            font-size: 13px;
            font-weight: 500;
            color: #1f2937;
            margin-bottom: 2px;
        }
        
        .stop-details {
            font-size: 11px;
            color: #6b7280;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .stop-details .arrival {
            color: #059669;
        }
        
        .stop-details .departure {
            color: #dc2626;
        }
        
        .stop-details .platform {
            color: #7c3aed;
        }
        
        /* Station trains section styling */
        .station-trains-section {
            margin-top: 12px;
            border-top: 1px solid #e5e7eb;
            padding-top: 12px;
        }
        
        .station-trains-section h4 {
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
            color: #374151;
        }
        
        .station-trains-list {
            max-height: 150px;
            overflow-y: auto;
        }
        
        .station-train {
            padding: 6px 0;
            border-bottom: 1px solid #f3f4f6;
            font-size: 12px;
        }
        
        .station-train:last-child {
            border-bottom: none;
        }
        
        .train-service-small {
            background: #3b82f6;
            color: white;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 6px;
        }
        
        .delay-small {
            background: #ef4444;
            color: white;
            padding: 1px 3px;
            border-radius: 3px;
            font-size: 9px;
            margin-left: 6px;
        }
        
        .platform-small {
            background: #7c3aed;
            color: white;
            padding: 1px 3px;
            border-radius: 3px;
            font-size: 9px;
            margin-left: 6px;
        }
        
        /* Better interaction feedback for overlapping elements */
        .train-marker:hover .train-icon {
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4), 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        
        .station-marker:hover .station-icon {
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4), 0 0 0 2px rgba(29, 78, 216, 0.2);
        }
        
        .station-marker:hover .station-icon-major {
            box-shadow: 0 6px 16px rgba(29, 78, 216, 0.4), 0 0 0 3px rgba(29, 78, 216, 0.3);
        }
        
        /* Ensure popups don't interfere with map interaction */
        .mapboxgl-popup-tip {
            border-top-color: rgba(255, 255, 255, 0.95) !important;
        }
        
        .station-symbol {
            font-size: 14px;
            line-height: 1;
        }
        
        /* Enhanced Popup Styles */
        .train-popup {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .train-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .train-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
        }
        
        .service-badge {
            background: #3b82f6;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .train-status {
            margin-bottom: 12px;
        }
        
        .delay-text {
            color: #ef4444;
            font-weight: 600;
        }
        
        .on-time-text {
            color: #10b981;
            font-weight: 600;
        }
        
        .platform {
            margin-top: 4px;
            font-size: 14px;
            color: #6b7280;
        }
        
        .train-route {
            margin-bottom: 12px;
            padding: 8px;
            background: #f9fafb;
            border-radius: 6px;
        }
        
        .route-info {
            font-size: 14px;
            line-height: 1.4;
        }
        
        .current-station, .next-station {
            margin: 8px 0;
            padding: 6px;
            background: #f3f4f6;
            border-radius: 4px;
            font-size: 13px;
        }
        
        .current-station {
            border-left: 3px solid #10b981;
        }
        
        .next-station {
            border-left: 3px solid #3b82f6;
        }
        
        .train-actions {
            margin-top: 12px;
            text-align: center;
        }
        
        .route-button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .route-button:hover {
            background: #2563eb;
        }
        
        .station-popup {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 280px;
        }
        
        .station-header {
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .station-header h3 {
            margin: 0 0 4px 0;
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
        }
        
        .station-type {
            font-size: 12px;
            color: #6b7280;
            font-weight: 500;
        }
        
        .station-info {
            margin-bottom: 8px;
        }
        
        .station-id, .trains-status {
            font-size: 13px;
            margin: 4px 0;
        }
        
        .trains-status {
            color: #10b981;
            font-weight: 500;
        }
        
        .station-coordinates {
            color: #9ca3af;
            font-size: 11px;
        }
        
        .train-status-info, .occupancy-info {
            margin: 4px 0;
            font-size: 13px;
            color: #374151;
        }
        
        .trains-list {
            margin-top: 8px;
            max-height: 120px;
            overflow-y: auto;
        }
        
        .station-train {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 0;
            border-bottom: 1px solid #f3f4f6;
            font-size: 12px;
        }
        
        .train-service-small {
            background: #3b82f6;
            color: white;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            min-width: 24px;
            text-align: center;
        }
        
        .delay-small {
            color: #ef4444;
            font-weight: 600;
            font-size: 10px;
        }
        
        .more-trains {
            color: #6b7280;
            font-style: italic;
            font-size: 11px;
            padding: 4px 0;
        }
        
        .station-actions {
            margin: 12px 0 8px 0;
            text-align: center;
        }
        
        .station-button {
            background: #10b981;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .station-button:hover {
            background: #059669;
        }
        
        /* Mapbox overrides for better performance */
        .mapboxgl-marker {
            will-change: transform;
            backface-visibility: hidden;
        }
        
        .mapboxgl-popup-content {
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 8px 12px;
        }
        
        .mapboxgl-popup-close-button {
            display: none !important;
        }
        
        /* Disable text selection on markers for better UX */
        .train-marker, .station-marker {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }
        
        /* Optimize map canvas performance */
        .mapboxgl-canvas {
            will-change: transform;
        }
        
        /* Reduce motion for users who prefer it */
        @media (prefers-reduced-motion: reduce) {
            .train-marker, .station-marker {
                transition: none;
            }
            .train-marker:hover, .station-marker:hover {
                transform: none;
            }
        }
        </style>
        ''')
        
        self._props['token'] = token

    def set_location(self, lng: float, lat: float, zoom: float):
        self.run_method('set_location', lng, lat, zoom)
        
    def add_train_marker(self, train_id: str, lng: float, lat: float, train_data: dict):
        self.run_method('add_train_marker', train_id, lng, lat, train_data)
        
    def add_station_marker(self, station_id: str, lng: float, lat: float, station_data: dict):
        self.run_method('add_station_marker', station_id, lng, lat, station_data)
        
    def add_stations_batch(self, stations_data: list):
        self.run_method('add_stations_batch', stations_data)
        
    def update_all_stations(self, stations_data: list):
        self.run_method('update_all_stations', stations_data)
        
    def update_trains(self, trains_data: list):
        self.run_method('update_trains', trains_data)
        
    def draw_route(self, coordinates: list, route_id: str = 'route'):
        self.run_method('draw_route', coordinates, route_id)
        
    def clear_route(self):
        self.run_method('clear_route')
        
    def clear_all_markers(self):
        self.run_method('clear_all_markers')

    # Legacy method for backward compatibility
    def add_marker(self, lng: float, lat: float, popup: str = ''):
        self.run_method('add_marker', lng, lat, popup)
    
    def draw_railway_lines(self, force_refresh: bool = False):
        """Draw railway lines on the map"""
        try:
            railway_data = railway_service.get_lines_for_map()
            if railway_data:
                self.run_method('draw_railway_lines', railway_data)
                logging.info(f"Drew railway lines: {sum(len(lines) for lines in railway_data.values())} total lines")
            else:
                logging.warning("No railway data available")
        except Exception as e:
            logging.error(f"Error drawing railway lines: {e}")
    
    def clear_railway_lines(self):
        """Clear all railway lines from the map"""
        self.run_method('clear_railway_lines')
    
    def highlight_railway_line(self, line_id: str):
        """Highlight a specific railway line"""
        self.run_method('highlight_railway_line', line_id) 