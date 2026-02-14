# TODO: Fix TripTracking creation - estimated_arrival must be passed to defaults

## Issue Identified:
In booking/views.py, there are 2 places where TripTracking.objects.get_or_create() is called
but the estimated_arrival is not being passed to the defaults parameter.

The bug is in:
1. trip_detail function (around line 346)
2. update_trip_location function (around line 400+)

The problematic code looks like:
```python
estimated_arrival = timezone.now() + timezone.timedelta(minutes=trip.duration) if trip.duration else timezone.now() + timezone.timedelta(minutes=15)
tracking, created = TripTracking.objects.get_or_create(
    trip=trip,
    # MISSING: defaults={'estimated_arrival': estimated_arrival}
)
```

## Fix Required:
Change to:
```python
tracking, created = TripTracking.objects.get_or_create(
    trip=trip,
    defaults={'estimated_arrival': estimated_arrival}
)
```

