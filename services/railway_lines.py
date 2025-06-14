#!/usr/bin/env python3

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import hashlib

@dataclass
class RailwayLine:
    """Represents a railway line with its properties"""
    id: str
    name: str
    coordinates: List[List[float]]  # [lng, lat] pairs
    line_type: str  # 'main', 'regional', 'urban', 'freight', 'historical'
    operator: str
    status: str  # 'active', 'inactive', 'under_construction'
    electrified: bool
    gauge: str  # 'iberian' (1668mm), 'metric' (1000mm), 'standard' (1435mm)
    max_speed: Optional[int]
    properties: Dict

class RailwayLinesService:
    """Service to fetch and manage Portuguese railway line data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.railway_lines = {}
        self.osm_data_cache = None
        self.last_update = None
        self.line_colors_cache = {}  # Cache for generated line colors
        
        # Portuguese railway line classifications - focused on train operations
        self.line_types = {
            'main': {
                'color': '#1B5E20',  # Dark green for main intercity lines
                'width': 5,
                'priority': 1
            },
            'regional': {
                'color': '#1565C0',  # Blue for regional lines
                'width': 3,
                'priority': 2
            },
            'urban': {
                'color': '#6A1B9A',  # Purple for urban train lines (Cascais/Sintra)
                'width': 3,
                'priority': 3
            },
            'freight': {
                'color': '#E65100',  # Orange for freight train lines
                'width': 2,
                'priority': 4
            }
        }
        
        # Major Portuguese railway lines
        self.major_lines = {
            'Linha do Norte': {
                'type': 'main',
                'description': 'Main line from Lisbon to Porto and Spanish border',
                'electrified': True,
                'gauge': 'iberian'
            },
            'Linha do Sul': {
                'type': 'main', 
                'description': 'Southern line to Algarve',
                'electrified': True,
                'gauge': 'iberian'
            },
            'Linha da Beira Alta': {
                'type': 'main',
                'description': 'Line to Spanish border via Guarda',
                'electrified': True,
                'gauge': 'iberian'
            },
            'Linha do Minho': {
                'type': 'main',
                'description': 'Northern line to Spanish border',
                'electrified': True,
                'gauge': 'iberian'
            },
            'Linha de Cascais': {
                'type': 'urban',
                'description': 'Lisbon suburban line to Cascais',
                'electrified': True,
                'gauge': 'iberian'
            },
            'Linha de Sintra': {
                'type': 'urban',
                'description': 'Lisbon suburban line to Sintra',
                'electrified': True,
                'gauge': 'iberian'
            }
        }
    
    def fetch_osm_railway_data(self) -> Optional[Dict]:
        """Fetch railway data from OpenStreetMap Overpass API - only proper train lines"""
        try:
            # Overpass API query for Portuguese railways - ONLY rail lines, excluding metro/tram/light_rail
            overpass_query = """
            [out:json][timeout:60];
            (
              way["railway"="rail"]["railway"!="abandoned"]["railway"!="disused"]
                 ["usage"!="industrial"]["service"!="siding"]["service"!="yard"]
                 (bbox:36.0,-10.0,42.5,-6.0);
            );
            out geom;
            """
            
            overpass_url = "http://overpass-api.de/api/interpreter"
            response = requests.post(overpass_url, data=overpass_query, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.osm_data_cache = data
                self.last_update = time.time()
                self.logger.info(f"Fetched {len(data.get('elements', []))} railway elements from OSM")
                return data
            else:
                self.logger.error(f"Failed to fetch OSM data: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching OSM railway data: {e}")
            return None
    
    def fetch_hdx_railway_data(self) -> Optional[Dict]:
        """Fetch railway data from Humanitarian Data Exchange"""
        try:
            # HDX Portugal Railways GeoJSON
            hdx_url = "https://data.humdata.org/dataset/hotosm_prt_railways"
            # Note: This would need the actual direct download URL for the GeoJSON file
            
            # For now, we'll use a placeholder - in real implementation,
            # you'd get the direct download URL from the HDX API
            self.logger.info("HDX railway data fetch not implemented yet")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching HDX railway data: {e}")
            return None
    
    def process_osm_data(self, osm_data: Dict) -> List[RailwayLine]:
        """Process OSM data into RailwayLine objects"""
        railway_lines = []
        
        try:
            for element in osm_data.get('elements', []):
                if element.get('type') == 'way' and 'geometry' in element:
                    tags = element.get('tags', {})
                    
                    # Extract coordinates
                    coordinates = []
                    for node in element['geometry']:
                        coordinates.append([node['lon'], node['lat']])
                    
                    if len(coordinates) < 2:
                        continue
                    
                    # Determine line type
                    railway_type = tags.get('railway', 'rail')
                    line_type = self._classify_line_type(tags)
                    
                    # Skip if not a proper train line
                    if line_type is None:
                        continue
                    
                    # Create RailwayLine object
                    line = RailwayLine(
                        id=f"osm_{element['id']}",
                        name=tags.get('name', f"Railway Line {element['id']}"),
                        coordinates=coordinates,
                        line_type=line_type,
                        operator=tags.get('operator', 'CP'),
                        status='active',
                        electrified=tags.get('electrified') in ['yes', 'contact_line'],
                        gauge=self._determine_gauge(tags),
                        max_speed=self._parse_max_speed(tags.get('maxspeed')),
                        properties=tags
                    )
                    
                    railway_lines.append(line)
                    
        except Exception as e:
            self.logger.error(f"Error processing OSM data: {e}")
        
        return railway_lines
    
    def _classify_line_type(self, tags: Dict) -> str:
        """Classify railway line type based on OSM tags - only for proper train lines"""
        railway = tags.get('railway', 'rail')
        usage = tags.get('usage', '')
        service = tags.get('service', '')
        name = tags.get('name', '').lower()
        operator = tags.get('operator', '').lower()
        
        # Skip non-train lines completely
        if railway != 'rail':
            return None
        
        # Skip industrial/service lines
        if usage in ['industrial', 'military'] or service in ['siding', 'yard', 'crossover']:
            return None
        
        # Main lines (major intercity routes operated by CP/IP)
        if (any(keyword in name for keyword in ['linha do norte', 'linha do sul', 'linha da beira alta', 'linha do minho', 'linha do leste', 'linha do oeste']) or
            usage == 'main' or
            'infraestruturas de portugal' in operator):
            return 'main'
        
        # Urban/suburban lines (but still proper train lines like Cascais/Sintra)
        if (any(keyword in name for keyword in ['cascais', 'sintra']) or
            usage in ['branch', 'regional'] and any(keyword in name for keyword in ['urbano', 'suburbano'])):
            return 'urban'
        
        # Freight lines (but still proper train lines)
        if usage == 'freight' or service == 'freight':
            return 'freight'
        
        # Regional lines (everything else that's a proper train line)
        if usage in ['branch', 'regional'] or railway == 'rail':
            return 'regional'
        
        # Default to regional for any remaining train lines
        return 'regional'
    
    def _determine_gauge(self, tags: Dict) -> str:
        """Determine track gauge from OSM tags"""
        gauge = tags.get('gauge', '')
        
        if '1668' in gauge:
            return 'iberian'
        elif '1000' in gauge:
            return 'metric'
        elif '1435' in gauge:
            return 'standard'
        else:
            # Default for Portugal is Iberian gauge
            return 'iberian'
    
    def _parse_max_speed(self, maxspeed: Optional[str]) -> Optional[int]:
        """Parse maximum speed from OSM tag"""
        if not maxspeed:
            return None
        
        try:
            # Remove 'km/h' and other units, extract number
            speed_str = maxspeed.replace('km/h', '').replace('mph', '').strip()
            return int(speed_str)
        except:
            return None
    
    def get_railway_lines(self, force_refresh: bool = False) -> List[RailwayLine]:
        """Get all railway lines, fetching fresh data for reliability"""
        
        # Always fetch fresh data for reliability (no complex caching)
        self.logger.info("Fetching fresh railway data...")
        osm_data = self.fetch_osm_railway_data()
        
        if osm_data:
            railway_lines = self.process_osm_data(osm_data)
            self.railway_lines = {line.id: line for line in railway_lines}
            self.logger.info(f"Fetched {len(railway_lines)} railway lines")
            return railway_lines
        
        # Return empty list if fetch failed
        self.logger.warning("No railway line data available")
        return []
    
    def _generate_unique_color(self, line_name: str) -> str:
        """Generate a unique color for a railway line based on its name"""
        if line_name in self.line_colors_cache:
            return self.line_colors_cache[line_name]
        
        # Use hash of line name to generate consistent color
        hash_object = hashlib.md5(line_name.encode())
        hex_dig = hash_object.hexdigest()
        
        # Extract RGB values from hash
        r = int(hex_dig[0:2], 16)
        g = int(hex_dig[2:4], 16) 
        b = int(hex_dig[4:6], 16)
        
        # Ensure colors are vibrant and distinguishable
        # Boost saturation and adjust brightness
        max_val = max(r, g, b)
        if max_val < 128:
            # Boost all values proportionally
            factor = 180 / max_val
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
        
        # Ensure minimum contrast
        if r + g + b < 200:
            # Add some brightness
            r = min(255, r + 50)
            g = min(255, g + 50)
            b = min(255, b + 50)
        
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.line_colors_cache[line_name] = color
        return color

    def get_lines_for_map(self) -> Dict:
        """Get railway lines formatted for map display with unique colors per line"""
        lines = self.get_railway_lines()
        
        # Group lines by type for layered display
        lines_by_type = {}
        for line in lines:
            line_type = line.line_type
            if line_type not in lines_by_type:
                lines_by_type[line_type] = []
            
            # Generate unique color for this specific line
            unique_color = self._generate_unique_color(line.name)
            
            # Get base style from line type but override color
            base_style = self.line_types.get(line_type, self.line_types['regional']).copy()
            base_style['color'] = unique_color
            
            # Format for map display
            line_data = {
                'id': line.id,
                'name': line.name,
                'coordinates': line.coordinates,
                'type': line_type,
                'style': base_style,
                'properties': {
                    'operator': line.operator,
                    'electrified': line.electrified,
                    'gauge': line.gauge,
                    'max_speed': line.max_speed,
                    'status': line.status
                }
            }
            
            lines_by_type[line_type].append(line_data)
        
        return lines_by_type
    
    def get_line_info(self, line_id: str) -> Optional[RailwayLine]:
        """Get detailed information about a specific railway line"""
        return self.railway_lines.get(line_id)

# Create a single instance
railway_service = RailwayLinesService() 