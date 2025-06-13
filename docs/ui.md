# UI/UX Vision & Design Blueprint

This document outlines the conceptual and visual plan for the CP Train Data application. The core philosophy is to create an interface that is **fast, simple, and highly interactive**, prioritizing the user's need to get critical train information (like platform numbers and delays) with zero friction.

We will focus on two main components: a **hyper-fast station search** and a **live, interactive station dashboard**.

---

## Component 1: The Station Search

The entry point to the application should be simple: finding a station.

### User Need
"I need to find my station (e.g., Lisboa Oriente) instantly."

### Concept & Behavior
-   A single, prominent search bar is the main element on the landing page.
-   As the user types, a list of matching station names appears instantly below the search bar. The search should be fuzzy and forgiving of typos.
-   Clicking a station name immediately navigates the user to the "Station Dashboard" for that station.

### Technical & Efficiency Strategy
-   To ensure "instant" search without spamming the API, the application will fetch the `/sites/spring/station-index` endpoint **once** when the web app is first loaded.
-   This list of ~300 stations and their IDs will be cached on the client-side (in the browser's memory).
-   The search bar will perform a client-side search against this cached list, using a lightweight library (like Fuse.js or even a simple array filter) to provide instantaneous results.
-   This approach is extremely fast for the user and results in only a single, small API call for the station list per user session.

---

## Component 2: The Live Station Dashboard

This is the heart of the application. Once a station is selected, this dashboard provides a live, at-a-glance view of all activity.

### User Need
"I'm at the station. Where is my train? Which platform? Is it on time?"

### Concept: A Dynamic, Easy-to-Read Timetable
The dashboard will present the train data from `/sites/spring/station/trains?stationId={stationId}` in a way that's easier to parse than a standard table.

#### Data Presentation
The information for each train should be grouped and prioritized visually. For each train, we'll display:

1.  **Direction & Destination (Primary Info):**
    -   Large, clear text: **"To Porto Campanha"** or **"From Faro"**.
    -   An icon (e.g., `->` for departure, `<-` for arrival) to make the direction immediately obvious.

2.  **Time & Delay (Critical Info):**
    -   **Estimated Time:** Display the `eta` (Estimated Time of Arrival) or `etd` (Estimated Time of Departure) most prominently. This is the time the user *actually* cares about.
    -   **Scheduled Time:** Show the original `arrivalTime` or `departureTime` in a smaller font or struck-through if there's a delay.
    -   **Delay:** A clear, color-coded status indicator.
        -   **On Time:** (Green) `delay` is 0 or `null`.
        -   **Delayed:** (Orange/Red) `+X min`. Display the `delay` value directly.

3.  **Platform (Essential Info):**
    -   A visually distinct element for the `platform` number (e.g., a colored box), making it easy to spot. This is one of the most critical pieces of information for a traveler.

4.  **Train Details (Secondary Info):**
    -   Train `service` (AP, IC, U, etc.) and `trainNumber`.
    -   `occupancy` level, if available, represented by simple icons (e.g., 1-3 signal bars).

#### Interaction & "Live" Feel
-   **Auto-Refresh:** The dashboard will automatically fetch fresh data from the endpoint every 30 seconds.
-   **Smooth Updates:** When new data arrives, the UI should update smoothly. Instead of a jarring full-page reload, changed elements (like a new delay or platform) can be subtly highlighted for a moment to draw the user's attention.
-   **Sorting:** Trains should be automatically sorted by their estimated time, with the next upcoming train always at the top.
-   **Filtering:** Simple buttons or tabs to filter the view by **Departures** and **Arrivals**.

### Visualization Idea: Platform-Centric View

To directly answer "which line is my train on?", we could offer an alternative visualization:

-   Instead of a list of trains, the UI could be a diagram of the station's platforms.
-   Each platform (`Linha 1`, `Linha 2`, etc.) would be a horizontal lane.
-   Train information cards would slide into the appropriate lane as they are assigned a platform.

**Example:**

```
[ Linha 1 ]──[ IC #523 to Porto @ 15:39 ]────────────────────────
[ Linha 2 ]──────────────────────────────────────────────────────
[ Linha 3 ]──[ Urbano #18282 to Sintra @ 15:38 ]───────────────────
[ Linha 4 ]──[ Urbano #16026 from Azambuja @ 15:45 ]───────────────
```

This view is highly intuitive and provides spatial awareness that a simple table cannot.

---

## Component 3: Train Drill-Down (Future)

While the station view is the priority, clicking on a specific train could navigate to a "Train Details" view.

-   **Concept:** A vertical timeline showing all stops for that train's journey.
-   **Live Element:** A marker would show the train's last reported position between two stations, potentially plotted on a small map using the `latitude` and `longitude` from the train details endpoint.

This blueprint provides a clear path forward for creating a highly usable and visually appealing application that solves the core problems of the user. 