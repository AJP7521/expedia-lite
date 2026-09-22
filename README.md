# Expedia Lite: Sample Data

These four CSV files contain fictional classroom data for a small travel application. All hotel names, travelers, bookings, and prices are invented. City names are real. The files do not describe live hotel availability or real reservations.

| File | One row represents | Rows | Unique ID |
| --- | --- | --- | --- |
| `hotels.csv` | One hotel | 8 | `hotel_id` |
| `users.csv` | One demo traveler | 6 | `user_id` |
| `trips.csv` | One offered hotel stay with fixed dates | 12 | `trip_id` |
| `bookings.csv` | One simulated reservation by a traveler for a trip | 6 | `booking_id` |

## Start with the CSV files

In this project, the four supplied CSV files are stored in `backend/data/`.

### Run the city search

The city search is implemented. The backend searches SQLite records seeded from `hotels.csv` and `trips.csv`, joins records by `hotel_id`, and calculates nights and stay prices. Vue sends a request to `GET /api/trips?city=Boston` and displays the returned JSON array. Matching ignores capitalization and surrounding spaces but requires a complete city name. Missing or blank city queries return HTTP 422; cities without matches return an empty array. The page distinguishes initial, loading, validation, no-results, and request-error states.

From the project root, start the backend with the existing virtual environment:

```sh
cd backend
.venv/bin/python -m uvicorn app.main:app --reload
```

In a second terminal, from the project root:

```sh
cd frontend
npm run dev
```

Open the URL printed by Vite. Its development proxy forwards `/api` requests to `http://127.0.0.1:8000`. Production hosting needs equivalent API routing; `npm run preview` alone does not provide that proxy.

Each result contains `trip_id`, `hotel_id`, `trip_name`, `hotel_name`, `city`, `state`, `check_in`, `check_out`, `nights`, `nightly_rate_usd`, and `stay_price_usd`. Money is calculated with decimal arithmetic on the backend and sent as JSON numbers; Vue formats it as USD. Sample CSV files are read only. Search and simulated bookings use SQLite.

### Simulated bookings and history

Search for a city and click **Book simulated stay**. The new confirmed booking appears in your history. Create an account and log in before searching or booking. The app shows your signed-in username and a Log out button. **Cancel booking** changes its status to cancelled while retaining the record. **Delete test booking** asks for confirmation and permanently removes the record. All these actions are available through the frontend and use relative `/api` requests. No real reservations or payments occur. Each signed-in account has its own booking history.

The backend creates `backend/data/expedia.sqlite3` on the first data request and imports all four supplied CSVs once in a transaction, preserving their IDs and relationships. Older hotels/trips-only databases receive the user and booking seeds through a one-time migration that keeps existing records on ID conflicts. Changes persist across refreshes and server restarts. Existing demo users and bookings are preserved in older databases but are not shown or editable through the app. The six seeded users and six bookings remain stored with their original ownership. New accounts start with empty history; existing seed and legacy bookings retain their original owners. Seed records are not a limit: new bookings receive UUID-based IDs and are stored in SQLite. After seeding, reads and writes use SQLite, and restarting does not restore deleted seeds or undo edits. Set `EXPEDIA_DB_PATH` to use a different SQLite file (its parent directory must exist). Database files are ignored by Git. SQLite uses Python's existing standard library; no additional dependency is needed.

API routes: `GET /api/bookings`, `POST /api/bookings` with `trip_id`, `PATCH /api/bookings/{booking_id}` with `status: "cancelled"`, and `DELETE /api/bookings/{booking_id}`. Invalid references return 404; invalid inputs return 422.

To verify through the frontend: create an account, log in, search Boston, create a simulated booking, find it in history, cancel it, refresh and confirm it remains cancelled, then delete that test booking and confirm it disappears. Backend tests use isolated temporary SQLite files and do not change live booking data.

Checks, each started from the project root:

```sh
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm run lint && npm run build)
```

For Part 1, the Python backend reads the supplied CSV files. The Vue frontend sends a search request through the FastAPI routes, and displays matching trips in a plain table. Hotel and trip information are connected by `hotel_id`. The sample users and bookings support the later booking and history work.

In this simplified model, a **trip is a hotel stay**. Each trip names one hotel and a check-in/check-out date. Flights, room inventory, authentication, payments, taxes, and fees are outside the data model. Each trip has a fixed nightly price from its hotel. The same hotel may appear in several trips with different dates.

For Part 2, these CSVs become the initial records in SQLite. Changes made in the application should be stored in the database. Restarting the application should preserve those changes. Re-importing the starter files on every startup must not erase new bookings, restore deleted bookings, or duplicate the sample records.

## Open the files in Excel

1. Extract the ZIP, then open each `.csv` file in Excel. The first row contains column names. Widen or AutoFit the columns so the full names and dates are visible.
2. If all values appear in one column or characters look wrong, use Excel’s text/CSV import and select **UTF-8** encoding and a **comma** delimiter.
3. Treat IDs such as `H001` as text. Preserve their letters and leading zeros. Dates in the files use `YYYY-MM-DD`; Excel may display them differently without changing their meaning.
4. Explore a copy when sorting or editing. Keep the supplied filenames and column names available to the application. Do not replace a CSV with an `.xlsx` workbook by changing the extension.

The CSV files are UTF-8 with a byte-order mark to help Excel recognize the encoding. Python can read them with `encoding="utf-8-sig"` so the mark does not become part of the first column name. Rates use a decimal point, without a currency symbol or thousands separator. CSV stores text values; the application interprets dates and numbers as needed.

## How the IDs connect

![Relationships: hotels.hotel_id connects to trips.hotel_id; trips.trip_id connects to bookings.trip_id; users.user_id connects to bookings.user_id. Each source row can be referenced by several rows in the related file.](relationships.png)

- `trips.hotel_id` matches a `hotel_id` in `hotels.csv`.
- `bookings.user_id` matches a `user_id` in `users.csv`.
- `bookings.trip_id` matches a `trip_id` in `trips.csv`.

A file’s **unique ID** identifies one row in that file. An ID used to refer to another file is a **foreign key**. For example, `H001` appears once in `hotels.csv`, but several trips can refer to `H001`. Repeated references are expected.

Each booking has two references: a traveler ID and a trip ID. They connect the traveler to the selected trip. The booking still has its own `booking_id`, so the application can update or delete that specific reservation.

## Data dictionary

### `hotels.csv`

| Column | Meaning | Example |
| --- | --- | --- |
| `hotel_id` | Unique text ID for the hotel | `H001` |
| `hotel_name` | Fictional hotel name | Harbor Lantern Hotel |
| `city` | Searchable destination city | Boston |
| `state` | State or district abbreviation | MA |
| `nightly_rate_usd` | Price of one room for one night, in U.S. dollars | `150` |

### `users.csv`

| Column | Meaning | Example |
| --- | --- | --- |
| `user_id` | Unique text ID for the demo traveler | `U001` |
| `display_name` | Fictional label shown in the application | Demo Traveler 1 |

These are demonstration identities, not login accounts. No passwords or personal contact details are provided.

### `trips.csv`

| Column | Meaning | Example |
| --- | --- | --- |
| `trip_id` | Unique text ID for an offered stay | `T001` |
| `hotel_id` | Reference to the hotel for this trip | `H001` |
| `trip_name` | Short title for the offered stay | Boston Harbor Weekend |
| `check_in` | First day of the stay | `2026-09-18` |
| `check_out` | Departure day; no overnight stay on this date | `2026-09-20` |

The number of nights is the number of days from check-in to check-out. For `T001`, September 18–20 is **two nights**. Its estimated stay price is **2 × $150 = $300**. This amount is derived from the trip dates and hotel rate; it is not stored in a second CSV column.

### `bookings.csv`

| Column | Meaning | Example |
| --- | --- | --- |
| `booking_id` | Unique text ID for one reservation | `B001` |
| `user_id` | Reference to the traveler making the reservation | `U001` |
| `trip_id` | Reference to the selected offered stay | `T001` |
| `booked_on` | Date when this example reservation was made | `2026-09-01` |
| `status` | `confirmed` or `cancelled` | `confirmed` |

Changing a booking’s status to `cancelled` keeps the row for history. Deleting a booking removes the row. These are different operations. Any new booking needs a new `booking_id`; existing IDs should stay unchanged.

## Concrete records to check

The following examples use a city search that ignores capitalization. Ordering of the returned rows is not significant.

| City query | Expected trip IDs | Count |
| --- | --- | --- |
| `Boston` or `boston` | `T001`, `T002`, `T009`, `T010` | 4 |
| `New York` | `T003`, `T004`, `T011` | 3 |
| `Philadelphia` | `T005`, `T006` | 2 |
| `Washington` | `T007`, `T012` | 2 |
| `State College` | `T008` | 1 |
| `Miami` | No matching rows | 0 |

An empty search field and a city with no results are different situations. The interface should make its handling of both understandable.

For a Boston search, these are the joined values behind a possible plain results table:

| Trip ID | Hotel | Check-in | Check-out | Nights | Nightly rate | Stay price |
| --- | --- | --- | --- | --- | --- | --- |
| `T001` | Harbor Lantern Hotel | 2026-09-18 | 2026-09-20 | 2 | $150 | $300 |
| `T002` | Maple Square Inn | 2026-09-18 | 2026-09-21 | 3 | $120 | $360 |
| `T009` | Harbor Lantern Hotel | 2026-10-02 | 2026-10-04 | 2 | $150 | $300 |
| `T010` | Maple Square Inn | 2026-10-09 | 2026-10-12 | 3 | $120 | $360 |

One booking connects all four files:

**`B001` → `U001` + `T001` → `H001`**

`B001` belongs to **Demo Traveler 1** (`U001`), for **Boston Harbor Weekend** (`T001`), at **Harbor Lantern Hotel** (`H001`). It is confirmed, was booked on September 1, and covers September 18–20 at an estimated stay price of **$300**.

Before making any changes, Demo Traveler 1 has two history rows: `B001` (confirmed) and `B002` (cancelled). Demo Traveler 6 (`U006`) has **no bookings**, providing an example of an empty history. Across the starter data, there are four confirmed and two cancelled bookings.

## Thursday: check SQLite before installing anything

Follow **CHECK → TAKE ACTION → VERIFY** in the project’s Python environment.

- **CHECK:** Ask the agent to identify the project’s Python interpreter and check whether it can import `sqlite3`. It should report the interpreter and SQLite version.
- **TAKE ACTION:** If the import succeeds, skip installation. If it fails, ask the agent to explain the missing capability and propose the smallest environment-specific correction for approval. Do not assume that `pip install sqlite3` is the required step.
- **VERIFY:** Use the selected interpreter to create a small local SQLite file, save a sample row, close the connection, reopen the same file, and read the row back.

Python documents `sqlite3` as an optional standard-library module, and SQLite does not require a separate database server. The check determines whether the selected Python distribution already provides it. See the [Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html).

## Files in this pack

The pack contains the four CSVs, this guide, `relationships.png`, and its editable `relationships.svg` source. The diagram’s text alternative is the “How the IDs connect” section above. The instructor’s generator validates unique IDs, linked IDs, dates, and sample search results before packaging.

### Interface

The responsive interface includes an original compass-inspired SVG logo, destination shortcuts, illustrated hotel cards with total and nightly prices, and a My bookings section with status badges. Header links jump to search and booking history. All artwork is local SVG/CSS; no external images, fonts, or additional packages are required. The small simulation notice remains visible above search results.

### MVC architecture

The backend retains its `app` package so the existing launch command continues to work:

```text
frontend/src/                  View: Vue screens, interaction, CSS
backend/app/models/            Model: entities and API input/output schemas
backend/app/controllers/
  database.py                  SQLite lifecycle, reference checks, entity CRUD
  trips.py                     Search, nights, and price calculations
  bookings.py                  Single-user history and booking lifecycle
  errors.py                    Transport-independent controller errors
backend/app/main.py            HTTP adapter and response serialization
```

The supplied CSVs contain 8 hotels, 12 trips, 6 sample users, and 6 sample bookings. Each trip references one hotel (`hotel_id`); each booking references one user (`user_id`) and one trip (`trip_id`). Those references are valid and IDs are unique within each file. All four CSVs seed SQLite once. The local application user is stored in addition to the six supplied users.

Models validate dates, rates, IDs, and status. The database controller provides typed create, get/list, update, and delete methods for all four entities, checks references, and rejects deletion of referenced parents. Business controllers use these methods without SQL. The API exposes only the search and booking operations needed by the View; internal entity CRUD does not add administration screens or endpoints. Existing SQLite files and booking data remain compatible.

The complete contracts and dependency rules are recorded in `AGENTS.md`. Run `cd backend && .venv/bin/python -m pytest -q` to check CSV relationships, model validation, CRUD, reference protection, transaction rollback, persistence, and HTTP behavior.


### Accounts and login

On the account screen choose **Create an account**, enter a username and password, and optionally an email. After registration, log in. Duplicate usernames (case-insensitive) return clear feedback. Usernames allow letters, numbers, dots, underscores, and dashes. The header shows the signed-in username; **Log out** clears the current session and displayed account data.

The Users table is migrated in place to add `username`, `password`, and `email`, with a unique case-insensitive username index. Existing IDs, display names, and booking references are retained. Existing sample and local users have no credentials assigned; newly registered accounts receive unique IDs and do not inherit those bookings. Passwords are salted PBKDF2 hashes, not readable text, using Python's standard library without additional dependencies.

FastAPI sets an HttpOnly, SameSite=Strict cookie referring to a SQLite session lasting 24 hours. Login persists across refreshes and backend restarts until expiration or logout. Searches require login and are recorded in SQLite with the authenticated `user_id`; all booking actions are restricted to that same user. Account endpoints are `POST /api/accounts`, `POST /api/login`, `GET /api/account`, and `POST /api/logout`. The public Account response never includes passwords. This local HTTP configuration uses a non-Secure cookie; HTTPS deployment must set Secure.
