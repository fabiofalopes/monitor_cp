# CP API Reference

This document serves as the technical reference for the Comboios de Portugal (CP) public API endpoints used in this project.

## Endpoints and Data Structures

### 1. Station Index

Returns a list of all CP train stations and their corresponding IDs. This endpoint should be called once and the data cached on the client.

-   **Endpoint:** `https://www.cp.pt/sites/spring/station-index`
-   **Method:** `GET`
-   **Data Structure:** A JSON object where keys are station names (e.g., `"lisboa oriente"`) and values are station IDs (e.g., `"94-31039"`).

    ```json
    {
      "abrantes": "94-52001",
      "ademia": "94-36046",
      "afife": "94-18119",
      ...
    }
    ```

### 2. Trains per Station

Returns a list of trains arriving at or departing from a specific station. This is a real-time endpoint that should be polled periodically for live data.

-   **Endpoint:** `https://www.cp.pt/sites/spring/station/trains?stationId={stationId}`
-   **Method:** `GET`
-   **URL Parameter:** `stationId` (e.g., `94-31039` for Lisboa Oriente).
-   **Data Structure:** A JSON array of train objects.

    ```json
    [
      {
        "delay": 13,
        "trainOrigin": { "code": "94-29157", "designation": "Braga" },
        "trainDestination": { "code": "94-30007", "designation": "Lisboa Santa Apolonia" },
        "departureTime": "13:53",
        "arrivalTime": "13:52",
        "trainNumber": 720,
        "trainService": { "code": "IC", "designation": "Intercidades" },
        "platform": "8",
        "occupancy": null,
        "eta": "14:05",
        "etd": "14:06"
      },
      ...
    ]
    ```
    -   `delay`: Delay in minutes.
    -   `trainOrigin` / `trainDestination`: Station codes and names.
    -   `departureTime` / `arrivalTime`: Scheduled times.
    -   `trainNumber`: Unique identifier for the train.
    -   `trainService`: Type of train (AP, IC, R, U).
    -   `platform`: The designated platform.
    -   `eta` / `etd`: Estimated time of arrival/departure, including delay.

### 3. Train Details

Returns the full journey of a specific train, including all its stops and its real-time location.

-   **Endpoint:** `https://www.cp.pt/sites/spring/station/trains/train?trainId={trainId}`
-   **Method:** `GET`
-   **URL Parameter:** `trainId` (e.g., `720`).
-   **Data Structure:** A JSON object containing train details and an array of stops.

    ```json
    {
      "trainNumber": 720,
      "serviceCode": { "code": "IC", "designation": "Intercidades" },
      "delay": 13,
      "occupancy": null,
      "latitude": "38.800666",
      "longitude": "-9.097726",
      "status": "IN_TRANSIT",
      "trainStops": [
        {
          "station": { "code": "94-29157", "designation": "Braga" },
          "arrival": null,
          "departure": "10:06",
          "platform": "1",
          "latitude": "41.547874450683594",
          "longitude": "-8.43464183807373",
          "delay": 2,
          "eta": null,
          "etd": "10:08"
        },
        ...
      ]
    }
    ```
    -   `latitude` / `longitude`: Real-time GPS coordinates of the train.
    -   `status`: Current status (e.g., `IN_TRANSIT`).
    -   `trainStops`: An array of all stations in the train's journey, with arrival/departure times and platform info. 