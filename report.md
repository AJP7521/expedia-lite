# Expedia Lite Report
## Repository: https://github.com/AJP7521/expedia-lite
## Current Local Commit: e3b43df96c7c89ef36d68563f4e11f0b7c7125e1

## Implementation

- Expedia Lite is a travel agent designed for finding hotel stays an managing simulated bookings. Users can create accounts using a username and password that saves their booking history and cancellations. Users can search cities, create bookings, review their history, cancel bookings, and delete test bookings.

- The Vue Frontend handles search inputs, API requests, results, and each user's booking history. It also displays how much a booking is, if a booking is confirmed, and errors if a booking isn't found or a login issue is detected.

- FastAPI provides the HTTP interface and authenticates accounts with session cookies.

- The Python Backend seperates models, controllers, and database access. Models handle request and response schemas. Controllers handle authentication for cities that are in the database, pricing, and the ability to book a reservation. The database controller handles the SQLite transactions. 

## Verification

- Action: Create Account and Log in.
- Expected Result: Account is created and signed-in username appears
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/7dcf50a3b38bbc80c966c683066873771160e6d8/Login%20Page.png)

- Action: Search Philadelphia 
- Expected Result: Two bookings: Liberty Lan inn and Museum Walk Hotel
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/5fb05bbd311de3c3f8c73591d23986078d885ee8/Login%20Page.png)

- Action: Blank Search
- Expected Results: No bookings are shown
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/d44364c3e57c53f7d8033101a6930a7292b72cfe/Blank%20Search.png)

- Action: Create booking
- Expected Results: Confirm booking in account history
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/7dcf50a3b38bbc80c966c683066873771160e6d8/Search%20Results.png)

- Action: Delete Booking
- Expected Results: Booking disapears from account history
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/e8676f14ed605076d465572d7e59562d49530f78/Delete%20Booking.png)

- Action: Log out
- Expected Result: Account is logged out and sign in/ sign up page is displayed
- Observed Result: ![image alt](https://github.com/AJP7521/expedia-lite/blob/e8676f14ed605076d465572d7e59562d49530f78/Log%20Out.png)

## Video Demo

- https://github.com/user-attachments/assets/5c2d172f-8da7-47e2-a000-cc283376c2d7
