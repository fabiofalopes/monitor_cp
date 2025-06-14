# Live Train Map Feature

## Overview

The live train map provides real-time visualization of Portuguese trains using data from the CP (Comboios de Portugal) API. The map displays active trains with custom icons, major stations, and interactive route visualization.

## Features

### 🚂 Real-Time Train Tracking
- **Live GPS Coordinates**: Trains are displayed at their actual real-time locations
- **Service Type Icons**: Different visual styles for IC (Intercidades), AP (Alfa Pendular), R (Regional), and U (Urbano) trains
- **Delay Indicators**: Color-coded markers showing on-time (green), minor delays (orange), and significant delays (red)
- **Train Information**: Service code, train number, and delay information displayed on markers

### 🚉 Station Display
- **Major Stations**: Key Portuguese stations (Lisboa Oriente, Porto Campanha, Faro, Coimbra-B, etc.)
- **Interactive Popups**: Click stations to see station information
- **Strategic Coverage**: Stations selected to provide comprehensive network coverage

### 🗺️ Interactive Route Visualization
- **Click-to-View Routes**: Click any train marker to display its complete route
- **Origin to Destination**: Full journey path with all intermediate stops
- **Route Highlighting**: Blue route lines with automatic map fitting
- **Clear Route**: Routes clear when clicking different trains

### ⚡ Performance Optimizations
- **Efficient Updates**: Only updates changed train positions
- **Marker Management**: Automatic cleanup of inactive trains
- **Background Processing**: Non-blocking data fetching every 10 seconds
- **Error Handling**: Graceful degradation when API is unavailable

## Technical Implementation

### Data Sources
The map integrates with three CP API endpoints:

1. **Station Index**: `https://www.cp.pt/sites/spring/station-index`
   - Loads all station names and IDs
   - Used for station identification and mapping

2. **Station Trains**: `https://www.cp.pt/sites/spring/station/trains?stationId={id}`
   - Fetches trains at specific stations
   - Provides basic train information and schedules

3. **Train Details**: `https://www.cp.pt/sites/spring/station/trains/train?trainId={id}`
   - Gets detailed train information including GPS coordinates
   - Provides complete route with all stops

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main App      │    │  TrainDataService │    │   CP API        │
│   (main.py)     │◄──►│  (Background)     │◄──►│   Endpoints     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   Map Component │    │   Data Processing│
│   (Vue.js)      │    │   & Validation   │
└─────────────────┘    └──────────────────┘
```

### Custom Styling

#### Train Markers
- **Shape**: Rounded rectangles with service code and train number
- **Colors**: 
  - Green border/background: On-time trains
  - Orange border/background: Minor delays (1-5 minutes)
  - Red border/background: Significant delays (>5 minutes)
- **Content**: Service code (IC, AP, R, U) and train number
- **Delay Badge**: Red circular indicator showing delay in minutes

#### Station Markers
- **Shape**: Circular icons with train emoji
- **Style**: White background with gray border
- **Interaction**: Hover effects and click popups

#### Route Lines
- **Color**: Blue (#3b82f6)
- **Width**: 4px with rounded caps
- **Opacity**: 80% for subtle overlay
- **Animation**: Smooth transitions when routes change

### Data Processing Pipeline

1. **Station Querying**: Query major stations for active trains
2. **Train Discovery**: Collect unique train IDs from all stations
3. **Detail Fetching**: Get GPS coordinates and route for each train
4. **Validation**: Ensure coordinates are within Portugal bounds
5. **Processing**: Format data for map display
6. **Update**: Efficiently update map markers

### Error Handling & Resilience

- **API Timeouts**: 10-second timeout with graceful fallback
- **Invalid Data**: Coordinate validation and filtering
- **Network Issues**: Retry logic with exponential backoff
- **Missing Data**: Graceful handling of incomplete train information

## Usage

### Navigation
- **Zoom/Pan**: Standard map controls in top-right corner
- **Geolocation**: Blue location button to find your position
- **Full Screen**: Map fills entire viewport below header

### Interactions
- **Train Click**: Click any train to see its complete route
- **Station Click**: Click stations for information popup
- **Route Clearing**: Click different trains to change route display

### Real-Time Updates
- **Automatic Refresh**: Map updates every 10 seconds
- **Live Positions**: Train locations reflect real GPS data
- **Status Changes**: Delay indicators update in real-time

## Configuration

### Environment Variables
```bash
MAPBOX_TOKEN=your_mapbox_access_token_here
```

### Major Stations Monitored
- Lisboa Oriente (94-31039)
- Porto Campanha (94-2006)
- Faro (94-73007)
- Coimbra-B (94-36004)
- Lisboa Santa Apolónia (94-30007)
- Porto São Bento (94-1008)
- Braga (94-29157)
- Évora (94-83006)

## Performance Considerations

### Optimization Strategies
- **Selective Updates**: Only redraw changed markers
- **Coordinate Validation**: Filter invalid GPS data
- **Memory Management**: Clean up inactive train markers
- **API Rate Limiting**: Respectful 10-second update intervals

### Scalability
- **Marker Limits**: Efficiently handles 50-100+ simultaneous trains
- **Route Complexity**: Supports routes with 20+ stops
- **Update Frequency**: Balances real-time accuracy with performance

## Future Enhancements

### Planned Features
- **Train Filtering**: Filter by service type, delay status, or route
- **Historical Data**: Show train punctuality trends
- **Notifications**: Alerts for specific trains or routes
- **Mobile Optimization**: Enhanced touch interactions
- **Offline Mode**: Cached data for limited connectivity

### Technical Improvements
- **WebSocket Integration**: Real-time push updates
- **Clustering**: Group nearby trains at low zoom levels
- **Route Prediction**: Estimated arrival times along routes
- **Performance Metrics**: Monitor API response times and accuracy

## Troubleshooting

### Common Issues

**No trains visible:**
- Check internet connection
- Verify Mapbox token is valid
- Ensure CP API is accessible

**Trains not updating:**
- Check browser console for errors
- Verify background service is running
- Check API rate limiting

**Route not displaying:**
- Ensure train has valid route data
- Check coordinate validation
- Verify train is currently active

### Debug Information
Enable browser developer tools to see:
- API request/response logs
- Coordinate validation results
- Marker update operations
- Error messages and stack traces 