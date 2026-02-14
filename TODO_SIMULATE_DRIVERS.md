# TODO: Simulate 2 drivers per vehicle type

## Task
Modify the API endpoint `/api/booking/drivers/by-vehicle-type/` to always return 2 drivers per vehicle type, using simulated drivers when real drivers are insufficient.

## Steps

- [x] 1. Analyze the codebase and understand the API endpoint
- [x] 2. Confirm plan with user
- [x] 3. Modify `get_drivers_by_vehicle_type_api` in `booking/views.py`
- [x] 4. Add simulation logic to generate 2 drivers per vehicle type
- [x] 5. Test the implementation

## Implementation Details

The function `get_drivers_by_vehicle_type_api` in `movenow/booking/views.py` was modified to:
1. Get real available drivers for each vehicle type
2. If fewer than 2 drivers exist, generate simulated drivers with:
   - Simulated names (e.g., "Chauffeur Simulé 1", "Chauffeur Simulé 2")
   - Coordinates slightly offset from the search location
   - Realistic but fake vehicle details
   - is_available=True
3. Added new fields to the response:
   - `is_simulated`: indicates if a driver is simulated
   - `real_drivers_count`: count of real drivers
   - `simulated_drivers_count`: count of simulated drivers
   - `simulation`: overall flag indicating simulation is active
   - `message`: human-readable message about simulation

