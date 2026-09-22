# Expedia Lite Project Report

## Goal
Search fictional hotel stays by city.

## Architecture
- Python reads hotels.csv and trips.csv and joins them by hotel_id.
- FastAPI returns matching records as JSON.
- Vue handles search inputs, requests, and results presentation.

## Implemented Features
- Case-insensitive city search
- Hotel names, stay dates, nights, and prices
- Blank-input validation
- Loading, no-results, and request-error states

## API
GET /api/trips?city=Boston

## Verification
- 13 backend tests passed.
- Frontend lint and production build passed.
- Browser checks covered Boston, blank input, Miami, and backend failure.
- Two dependency deprecation warnings remain.

## Limitations
- Fictional sample data only.
- Booking operations and SQLite persistence are not implemented.