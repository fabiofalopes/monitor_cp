export default {
    template: `
        <div class="map-container">
            <div ref="mapElement" class="map-element"></div>
        </div>
    `,
    props: {
        token: String,
    },
    data() {
        return {
            trainMarkers: new Map(),
            stationMarkers: new Map(),
            currentRoute: null,
            isMapMoving: false,
            stationsLoaded: false,
        };
    },
    mounted() {
        mapboxgl.accessToken = this.token;
        this.map = new mapboxgl.Map({
            container: this.$refs.mapElement,
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [-8.61099, 41.14961], // Default to Portugal
            zoom: 6,
            // Optimize for performance
            antialias: false,
            preserveDrawingBuffer: false,
        });

        this.map.addControl(new mapboxgl.NavigationControl());
        this.map.addControl(new mapboxgl.GeolocateControl({
            positionOptions: {
                enableHighAccuracy: true
            },
            trackUserLocation: true,
            showUserHeading: true
        }));

        // Track map movement for performance optimization
        this.map.on('movestart', () => {
            this.isMapMoving = true;
        });

        this.map.on('moveend', () => {
            this.isMapMoving = false;
        });

        // Ensure map resizes properly when container changes
        this.$nextTick(() => {
            this.map.resize();
        });

        // Add resize observer to handle dynamic size changes
        if (window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(() => {
                if (!this.isMapMoving) {
                    this.map.resize();
                }
            });
            this.resizeObserver.observe(this.$refs.mapElement);
        }

        // Initialize route source for drawing train routes
        this.map.on('load', () => {
            this.map.addSource('route', {
                'type': 'geojson',
                'data': {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': []
                    }
                }
            });

            this.map.addLayer({
                'id': 'route',
                'type': 'line',
                'source': 'route',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#3b82f6',
                    'line-width': 4,
                    'line-opacity': 0.8
                }
            });
            
            // Setup global functions after map loads
            this.setupGlobalFunctions();
        });
    },
    beforeUnmount() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        if (this.map) {
            this.map.remove();
        }
    },
    methods: {
        set_location(lng, lat, zoom) {
            this.map.flyTo({
                center: [lng, lat],
                zoom: zoom,
                speed: 1.5,
            });
        },
        
        add_train_marker(trainId, lng, lat, trainData) {
            // Remove existing marker if it exists
            if (this.trainMarkers.has(trainId)) {
                this.trainMarkers.get(trainId).remove();
            }

            // Create custom train icon with proper anchoring
            const el = document.createElement('div');
            el.className = 'train-marker';
            el.innerHTML = this.createTrainIcon(trainData);
            
            // Create detailed popup for train information
            const popup = new mapboxgl.Popup({ 
                offset: 25,
                closeButton: false,
                closeOnClick: true,
                closeOnMove: false,
                maxWidth: '350px',
                className: 'train-popup-container'
            })
                .setHTML(this.createTrainPopupContent(trainData));

            // Create marker with proper anchor point
            const marker = new mapboxgl.Marker({
                element: el,
                anchor: 'center', // Ensure proper centering
                pitchAlignment: 'map', // Keep aligned with map
                rotationAlignment: 'map', // Keep aligned with map
                offset: [0, -5] // Slight offset to reduce overlap with stations
            })
                .setLngLat([lng, lat])
                .setPopup(popup)
                .addTo(this.map);
            
            // Add click handler for route visualization and popup
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                // Show popup first, then route
                marker.togglePopup();
                this.show_train_route(trainId, trainData);
            });

            this.trainMarkers.set(trainId, marker);
        },

        add_station_marker(stationId, lng, lat, stationData) {
            // Don't add duplicate station markers
            if (this.stationMarkers.has(stationId)) {
                return;
            }

            const el = document.createElement('div');
            el.className = 'station-marker';
            el.innerHTML = this.createStationIcon(stationData);

            const popup = new mapboxgl.Popup({ 
                offset: 25,
                closeButton: false,
                closeOnClick: true,
                closeOnMove: false,
                maxWidth: '300px',
                className: 'station-popup-container'
            })
                .setHTML(this.createStationPopupContent(stationData, stationId));

            // Create marker with proper anchor point and alignment
            const marker = new mapboxgl.Marker({
                element: el,
                anchor: 'center', // Proper centering
                pitchAlignment: 'map', // Stay aligned with map
                rotationAlignment: 'map', // Stay aligned with map
                offset: [0, 0] // No offset for stations - they should be precisely positioned
            })
                .setLngLat([lng, lat])
                .setPopup(popup)
                .addTo(this.map);
            
            // Add click handler to ensure popup shows
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                marker.togglePopup();
            });

            this.stationMarkers.set(stationId, marker);
        },

        createTrainIcon(trainData) {
            const serviceCode = trainData.serviceCode || 'T';
            const delay = trainData.delay || 0;
            const delayClass = delay > 5 ? 'delayed' : delay > 0 ? 'minor-delay' : 'on-time';
            
            return `
                <div class="train-icon ${delayClass}">
                    <div class="train-service">${serviceCode}</div>
                    <div class="train-number">#${trainData.trainNumber}</div>
                    ${delay > 0 ? `<div class="delay-indicator">+${delay}m</div>` : ''}
                </div>
            `;
        },

        createStationIcon(stationData) {
            const isMajor = stationData.type === 'major';
            const hasTrains = stationData.hasTrains;
            const iconClass = isMajor ? 'station-icon-major' : 'station-icon-regular';
            const statusClass = hasTrains ? 'has-trains' : 'no-trains';
            
            return `
                <div class="station-icon ${iconClass} ${statusClass}">
                    <div class="station-symbol">${isMajor ? '🚉' : '🚏'}</div>
                </div>
            `;
        },

        createTrainPopupContent(trainData) {
            const delay = trainData.delay || 0;
            const delayText = delay > 0 ? `<span class="delay-text">+${delay} min delay</span>` : '<span class="on-time-text">On time</span>';
            
            // Find current and next stations from trainStops
            let currentStationInfo = '';
            let nextStationInfo = '';
            
            if (trainData.trainStops && trainData.trainStops.length > 0) {
                const now = new Date();
                const currentTime = now.getHours() * 60 + now.getMinutes();
                
                let currentStation = null;
                let nextStation = null;
                
                for (let i = 0; i < trainData.trainStops.length; i++) {
                    const stop = trainData.trainStops[i];
                    const etd = stop.etd || stop.departure;
                    const eta = stop.eta || stop.arrival;
                    
                    if (etd && !stop.departed) {
                        const [hours, minutes] = etd.split(':').map(Number);
                        const stopTime = hours * 60 + minutes;
                        
                        if (stopTime > currentTime) {
                            nextStation = stop;
                            if (i > 0) currentStation = trainData.trainStops[i - 1];
                            break;
                        }
                    }
                }
                
                if (currentStation) {
                    currentStationInfo = `
                        <div class="current-station">
                            <strong>Current/Last:</strong> ${currentStation.station.designation}
                            ${currentStation.platform ? `<br><small>Platform ${currentStation.platform}</small>` : ''}
                            ${currentStation.etd ? `<br><small>Departed: ${currentStation.etd}</small>` : ''}
                        </div>
                    `;
                }
                
                if (nextStation) {
                    nextStationInfo = `
                        <div class="next-station">
                            <strong>Next:</strong> ${nextStation.station.designation}
                            ${nextStation.platform ? `<br><small>Platform ${nextStation.platform}</small>` : ''}
                            ${nextStation.eta ? `<br><small>ETA: ${nextStation.eta}</small>` : ''}
                        </div>
                    `;
                }
            }
            
            // Status information
            let statusInfo = '';
            if (trainData.status) {
                const statusMap = {
                    'IN_TRANSIT': '🚄 In Transit',
                    'AT_STATION': '🚉 At Station',
                    'DELAYED': '⏰ Delayed',
                    'CANCELLED': '❌ Cancelled',
                    'TERMINATED': '🏁 Terminated'
                };
                statusInfo = `<div class="train-status-info">Status: ${statusMap[trainData.status] || trainData.status}</div>`;
            }
            
            // Occupancy information
            let occupancyInfo = '';
            if (trainData.occupancy) {
                const occupancyMap = {
                    'LOW': '🟢 Low occupancy',
                    'MEDIUM': '🟡 Medium occupancy', 
                    'HIGH': '🔴 High occupancy',
                    'FULL': '🚫 Full'
                };
                occupancyInfo = `<div class="occupancy-info">${occupancyMap[trainData.occupancy] || trainData.occupancy}</div>`;
            }
            
            return `
                <div class="train-popup">
                    <div class="train-header">
                        <h3>${trainData.serviceName} #${trainData.trainNumber}</h3>
                        <div class="service-badge">${trainData.serviceCode}</div>
                    </div>
                    
                    <div class="train-status">
                        ${delayText}
                        ${trainData.platform ? `<div class="platform">Platform: ${trainData.platform}</div>` : ''}
                        ${statusInfo}
                        ${occupancyInfo}
                    </div>
                    
                    <div class="train-route">
                        <div class="route-info">
                            <strong>From:</strong> ${trainData.origin}<br>
                            <strong>To:</strong> ${trainData.destination}
                        </div>
                    </div>
                    
                    ${currentStationInfo}
                    ${nextStationInfo}
                    
                    ${this.createTrainStopsSection(trainData)}
                </div>
            `;
        },

        createTrainStopsSection(trainData) {
            if (!trainData.trainStops || trainData.trainStops.length === 0) {
                return '';
            }

            const stops = trainData.trainStops.map((stop, index) => {
                const isFirst = index === 0;
                const isLast = index === trainData.trainStops.length - 1;
                const eta = stop.eta || stop.arrival;
                const etd = stop.etd || stop.departure;
                const platform = stop.platform ? `Platform ${stop.platform}` : '';
                
                return `
                    <div class="train-stop ${isFirst ? 'first-stop' : ''} ${isLast ? 'last-stop' : ''}">
                        <div class="stop-name">${stop.station.designation}</div>
                        <div class="stop-details">
                            ${eta ? `<span class="arrival">Arr: ${eta}</span>` : ''}
                            ${etd ? `<span class="departure">Dep: ${etd}</span>` : ''}
                            ${platform ? `<span class="platform">${platform}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="train-stops-section">
                    <h4>Route (${trainData.trainStops.length} stops)</h4>
                    <div class="train-stops-list">
                        ${stops}
                    </div>
                </div>
            `;
        },

        createStationPopupContent(stationData, stationId) {
            const stationType = stationData.type === 'major' ? '🚉 Major Station' : '🚏 Station';
            
            // Count trains at this station
            let trainCount = 0;
            let trainsList = '';
            
            // Get trains from the current data (we'll need to pass this from the backend)
            if (stationData.trains && stationData.trains.length > 0) {
                trainCount = stationData.trains.length;
                trainsList = stationData.trains.map(train => 
                    `<div class="station-train">
                        <span class="train-service-small">${train.serviceCode}</span> 
                        #${train.trainNumber} → ${train.destination}
                        ${train.delay > 0 ? `<span class="delay-small">+${train.delay}m</span>` : ''}
                        ${train.platform ? `<span class="platform-small">Platform ${train.platform}</span>` : ''}
                    </div>`
                ).join('');
            }
            
            const trainsStatus = trainCount > 0 ? `${trainCount} active train${trainCount !== 1 ? 's' : ''}` : 'No active trains';
            
            return `
                <div class="station-popup">
                    <div class="station-header">
                        <h3>${stationData.name}</h3>
                        <div class="station-type">${stationType}</div>
                    </div>
                    
                    <div class="station-info">
                        <div class="trains-status">${trainsStatus}</div>
                        ${trainsList ? `
                            <div class="station-trains-section">
                                <h4>Active Trains</h4>
                                <div class="station-trains-list">
                                    ${trainsList}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="station-coordinates">
                        <small>Lat: ${stationData.lat.toFixed(4)}, Lng: ${stationData.lng.toFixed(4)}</small>
                    </div>
                </div>
            `;
        },

        show_train_route(trainId, trainData) {
            // Clear any existing route first
            this.clear_route();
            
            // Request route data from Python backend
            this.$emit('request_train_route', trainId);
        },
        
        // Global function for route button clicks
        setupGlobalFunctions() {
            window.showTrainRoute = (trainId) => {
                this.show_train_route(trainId);
            };
            
            window.showStationDetails = (stationId) => {
                // Navigate to station details or show more info
                this.$emit('show_station_details', stationId);
            };
        },

        draw_route(coordinates, routeId = 'route') {
            if (!coordinates || coordinates.length === 0) {
                return;
            }

            if (this.map.getSource(routeId)) {
                this.map.getSource(routeId).setData({
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates
                    }
                });

                // Fit map to show the entire route with padding
                const bounds = new mapboxgl.LngLatBounds();
                coordinates.forEach(coord => bounds.extend(coord));
                
                this.map.fitBounds(bounds, { 
                    padding: 50,
                    duration: 1000 // Smooth animation
                });
            }
        },

        clear_route() {
            if (this.map.getSource('route')) {
                this.map.getSource('route').setData({
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': []
                    }
                });
            }
        },

        clear_all_markers() {
            // Clear train markers
            this.trainMarkers.forEach(marker => marker.remove());
            this.trainMarkers.clear();
            
            // Clear station markers
            this.stationMarkers.forEach(marker => marker.remove());
            this.stationMarkers.clear();
            
            this.stationsLoaded = false;
        },

        update_trains(trainsData) {
            // Skip updates during map movement for better performance
            if (this.isMapMoving) {
                return;
            }

            // Efficiently update train markers
            const currentTrainIds = new Set(this.trainMarkers.keys());
            const newTrainIds = new Set();

            // Batch DOM updates for better performance
            requestAnimationFrame(() => {
                trainsData.forEach(train => {
                    newTrainIds.add(train.trainId);
                    this.add_train_marker(
                        train.trainId,
                        train.lng,
                        train.lat,
                        train
                    );
                });

                // Remove markers for trains that are no longer active
                currentTrainIds.forEach(trainId => {
                    if (!newTrainIds.has(trainId)) {
                        const marker = this.trainMarkers.get(trainId);
                        if (marker) {
                            marker.remove();
                            this.trainMarkers.delete(trainId);
                        }
                    }
                });
            });
        },

        // Optimized method for adding multiple stations at once
        add_stations_batch(stationsData) {
            // Skip updates during map movement
            if (this.isMapMoving) {
                return;
            }

            // Only add stations once to avoid duplicates
            if (this.stationsLoaded) {
                return;
            }

            // Batch DOM updates
            requestAnimationFrame(() => {
                stationsData.forEach(station => {
                    this.add_station_marker(
                        station.stationId,
                        station.lng,
                        station.lat,
                        station
                    );
                });
                this.stationsLoaded = true;
            });
        },

        // Method to update all stations (including discovered ones)
        update_all_stations(stationsData) {
            // Skip updates during map movement
            if (this.isMapMoving) {
                return;
            }

            // Clear existing stations and reload
            this.stationMarkers.forEach(marker => marker.remove());
            this.stationMarkers.clear();
            this.stationsLoaded = false;

            // Add all stations
            this.add_stations_batch(stationsData);
        },

        // Legacy method for backward compatibility
        add_marker(lng, lat, popup_text = '') {
            const marker = new mapboxgl.Marker({
                anchor: 'center',
                pitchAlignment: 'map',
                rotationAlignment: 'map'
            })
                .setLngLat([lng, lat])
                .addTo(this.map);
                
            if (popup_text) {
                const popup = new mapboxgl.Popup({ offset: 25 }).setText(popup_text);
                marker.setPopup(popup);
            }
        },

        // Railway lines functionality
        draw_railway_lines(railwayData) {
            if (!railwayData) return;
            
            // Remove existing railway layers
            this.clear_railway_lines();
            
            // Add railway lines by type (in order of priority - background to foreground)
            const lineTypes = ['freight', 'regional', 'urban', 'main'];
            
            lineTypes.forEach(lineType => {
                const lines = railwayData[lineType];
                if (!lines || lines.length === 0) return;
                
                // Create GeoJSON feature collection for this line type
                const features = lines.map(line => ({
                    type: 'Feature',
                    properties: {
                        id: line.id,
                        name: line.name,
                        type: line.type,
                        ...line.properties
                    },
                    geometry: {
                        type: 'LineString',
                        coordinates: line.coordinates
                    }
                }));
                
                const sourceId = `railway-${lineType}`;
                const layerId = `railway-${lineType}-layer`;
                
                // Add source
                this.map.addSource(sourceId, {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: features
                    }
                });
                
                // Add layer
                const style = lines[0].style;
                const layerConfig = {
                    id: layerId,
                    type: 'line',
                    source: sourceId,
                    layout: {
                        'line-join': 'round',
                        'line-cap': 'round'
                    },
                    paint: {
                        'line-color': style.color,
                        'line-width': style.width,
                        'line-opacity': 0.8
                    }
                };
                
                this.map.addLayer(layerConfig);
                
                // Add click handler for railway lines
                this.map.on('click', layerId, (e) => {
                    const properties = e.features[0].properties;
                    this.show_railway_popup(e.lngLat, properties);
                });
                
                // Change cursor on hover
                this.map.on('mouseenter', layerId, () => {
                    this.map.getCanvas().style.cursor = 'pointer';
                });
                
                this.map.on('mouseleave', layerId, () => {
                    this.map.getCanvas().style.cursor = '';
                });
            });
        },

        clear_railway_lines() {
            const lineTypes = ['main', 'regional', 'urban', 'freight'];
            
            lineTypes.forEach(lineType => {
                const sourceId = `railway-${lineType}`;
                const layerId = `railway-${lineType}-layer`;
                
                if (this.map.getLayer(layerId)) {
                    this.map.removeLayer(layerId);
                }
                if (this.map.getSource(sourceId)) {
                    this.map.removeSource(sourceId);
                }
            });
        },

        show_railway_popup(lngLat, properties) {
            const electrified = properties.electrified === 'true' ? '⚡ Electrified' : '🔌 Non-electrified';
            const gauge = properties.gauge === 'iberian' ? '🛤️ Iberian gauge (1668mm)' : 
                         properties.gauge === 'metric' ? '🛤️ Metric gauge (1000mm)' : 
                         properties.gauge === 'standard' ? '🛤️ Standard gauge (1435mm)' :
                         '🛤️ Unknown gauge';
            
            const maxSpeed = properties.max_speed ? `🚄 Max speed: ${properties.max_speed} km/h` : '';
            
            const typeDescriptions = {
                'main': 'Main intercity train line',
                'regional': 'Regional train line',
                'urban': 'Urban train line (Cascais/Sintra)',
                'freight': 'Freight train line'
            };
            
            const popupContent = `
                <div style="font-family: Arial, sans-serif; max-width: 280px;">
                    <h3 style="margin: 0 0 10px 0; color: #1976D2; font-size: 16px;">
                        🚂 ${properties.name}
                    </h3>
                    <div style="font-size: 14px; line-height: 1.4;">
                        <div style="margin-bottom: 5px;">
                            <strong>Type:</strong> ${typeDescriptions[properties.type] || properties.type}
                        </div>
                        <div style="margin-bottom: 5px;">
                            <strong>Operator:</strong> ${properties.operator || 'CP'}
                        </div>
                        <div style="margin-bottom: 5px;">${electrified}</div>
                        <div style="margin-bottom: 5px;">${gauge}</div>
                        ${maxSpeed ? `<div style="margin-bottom: 5px;">${maxSpeed}</div>` : ''}
                        <div style="margin-top: 10px; font-size: 12px; color: #666;">
                            Railway line information from OpenStreetMap
                        </div>
                    </div>
                </div>
            `;
            
            new mapboxgl.Popup({
                offset: 25,
                closeButton: false,
                closeOnClick: true,
                closeOnMove: false,
                maxWidth: '300px',
                className: 'railway-popup-container'
            })
                .setLngLat(lngLat)
                .setHTML(popupContent)
                .addTo(this.map);
        },

        highlight_railway_line(lineId) {
            // This could be used to highlight a specific railway line
            // when a train is selected, showing which line it's traveling on
            console.log(`Highlighting railway line: ${lineId}`);
            
            // Future enhancement: could add a highlighted layer for the specific line
        }
    },
}; 