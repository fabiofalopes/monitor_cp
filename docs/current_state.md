# Monitor CP

This project is a real-time train departure and arrival board for the Portuguese CP rail service, built with Python and the NiceGUI framework. It provides a fast, interactive, and data-rich interface for viewing live train information for any station in the country.

## Core Features

-   **Instant Station Search:** A fuzzy, client-side search allows users to find any of the ~460 CP stations instantly. The station list is fetched once on startup and cached, ensuring a snappy user experience.
-   **Platform-Centric Live Board:** Inspired by the vision in `ui.md`, the main dashboard displays train information grouped by platform. This provides a clear, at-a-glance view of all activity at the station.
-   **Responsive Grid Layout:** The platform cards are arranged in a responsive grid that adapts to different screen sizes, showing multiple columns on desktops and a single column on mobile devices for optimal use of space.
-   **Dynamic Filtering:** Users can filter the live board by train service type (e.g., Urbano, Intercidades) and by train number. The filters work independently and update the view in real-time as the user types or makes a selection.
-   **Detailed Train Information:** Each train card displays a wealth of information in a compact and easy-to-read format, including:
    -   Full service name and train number.
    -   Complete route (`Origin → Destination`).
    -   Real-time estimated departure/arrival time.
    -   Scheduled times, which are struck through if the train is delayed.
    -   Color-coded delay status (`On Time` or `+X min`).
-   **Interactive UI Elements:**
    -   A sticky "Go to platform" navigation bar allows for quick jumps to any platform section.
    -   A "scroll-to-top" button provides a convenient way to return to the top of the page.
-   **Auto-Refresh:** The dashboard automatically fetches fresh data every 30 seconds to ensure the information is always up-to-date.

## Development Journey

The application started from a conceptual blueprint in `ui.md` and was brought to life through an iterative development process. Key milestones and challenges included:

1.  **Initial Prototype:** The first version used a simple card layout with basic filtering. This was quickly identified as inefficient and not aligned with the "Platform-Centric" vision.
2.  **Major UI Overhaul:** The UI was completely redesigned to implement the platform-based grid layout. This process involved fixing a series of bugs related to the NiceGUI framework and its component APIs.
3.  **Refining the User Experience:** Through continuous feedback, several improvements were made:
    -   The search was transitioned from a basic input to NiceGUI's more powerful `ui.select` component.
    -   The layout was made fully responsive to better utilize screen real estate.
    -   The train cards were redesigned to be more data-dense and visually balanced.
    -   The filtering system was refined to be more dynamic and intuitive.

The project now stands as a polished and functional application that successfully realizes the initial vision laid out in `ui.md`. It serves as a strong foundation for any future enhancements, such as the "Train Drill-Down" feature originally conceptualized. 