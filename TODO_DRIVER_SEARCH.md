# TODO: Driver Search by Vehicle Type

## Task
"dans rechercher chauffeur met les chauffeurs pour chaque vehicule et lance le serveur"
- In driver search, show drivers for each vehicle type (grouped)
- Launch the server

## Steps

- [ ] 1. Modify book.html to use `/api/booking/drivers/by-vehicle-type/` endpoint
- [ ] 2. Update JavaScript to display drivers grouped by vehicle type
- [ ] 3. Test and launch the Django server

## Current Implementation
- book.html calls `/api/booking/drivers/search/` which only returns drivers for ONE vehicle type
- There's already an endpoint `/api/booking/drivers/by-vehicle-type/` that returns drivers grouped by vehicle type

## Changes Needed
- Update the API call in book.html to use the by-vehicle-type endpoint
- Update the display logic to show drivers grouped by vehicle type
