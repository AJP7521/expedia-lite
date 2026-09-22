# Project rules

## Scope and structure

- Build Expedia Agent as a FastAPI backend in `backend/` and a Vue frontend in `frontend/`.
- Keep Python application code in `backend/app/` and Vue application code in `frontend/src/`.
- Keep the scaffold minimal. Add features, integrations, and infrastructure only when the task calls for them.
- Keep backend routes under `/api` and use relative `/api` URLs in the frontend.

## Dependencies and configuration

- Do not install dependencies until the user authorizes installation.
- Declare Python dependencies in `backend/requirements.txt` and frontend dependencies in `frontend/package.json`.
- Never commit secrets, credentials, `.env` files, virtual environments, or `node_modules`.
- Keep external service credentials on the backend; never embed them in frontend code.

## Implementation and validation

- Use idiomatic Python and Vue single-file components; prefer simple, readable code.
- Preserve existing user changes and avoid unrelated refactors.
- Add appropriate tests when implementing substantive behavior. Do not claim checks passed unless they were run.
- Run relevant checks when dependencies are available; otherwise explain what could not be validated.
- Update `README.md` when setup, configuration, or user-visible behavior changes.
- Do not perform real bookings, payments, or other external commitments without explicit user authorization.

## MVC architecture and contracts

- Keep the existing Python package root: `backend/app/models/` is Model, `backend/app/controllers/` is Controller, and `frontend/src/` is View. `backend/app/main.py` is a thin HTTP adapter. This follows the sample MVC layout while preserving the project's `backend/app/` convention and startup command.
- Models define validated, immutable entity objects and request/response schemas using Pydantic. They must not import controllers, FastAPI, SQLite, or frontend code. Use `model_validate` or constructors for changed values; do not bypass validation with unchecked copies.
- CSV-derived entities: Hotel (`hotel_id`, `hotel_name`, `city`, `state`, `nightly_rate_usd`); Trip (`trip_id`, `hotel_id`, `trip_name`, `check_in`, `check_out`); User (`user_id`, `display_name`, `username`, `password`, optional `email`); Booking (`booking_id`, `user_id`, `trip_id`, `booked_on`, `status`). IDs are nonempty strings. Dates are ISO calendar dates. Rates use nonnegative finite Decimal values. Check-out must follow check-in. Status is `confirmed` or `cancelled`.
- Relationships: Hotel 1→many Trips; User 1→many Bookings; Trip 1→many Bookings. A booking links exactly one user and one trip. Never delete a referenced parent implicitly or cascade without an explicit requirement.
- Only `controllers/database.py` may open SQLite, execute SQL, create schemas, or import seed CSVs. Its `DatabaseController` context opens/closes the connection and commits on success or rolls back on error. Keep foreign keys enabled. Check references for both create and update. SQL identifiers must come from the fixed entity registry; parameterize all values.
- Database controller contract: `get(EntityClass, id) -> Entity`, `list(EntityClass) -> list[Entity]`, `create(Entity) -> Entity`, `update(Entity) -> Entity` (full replacement at the same primary key), `delete(EntityClass, id) -> None`. Only User, Hotel, Trip, and Booking are accepted. Missing entities/references raise `NotFoundError`; duplicate IDs or protected parent deletion raise `ConflictError`. Never return SQLite rows/connections to business controllers or the View. The low-level `connect()` is internal to persistence (tests may use it to construct legacy fixtures).
- Business rules live in separate controllers. `trips.search_trips(city, user_id) -> list[TripResult]` trims and matches complete city names case-insensitively; blank input raises ValueError. `trips.describe_trip(db, Trip) -> TripResult` calculates nights and totals with Decimal arithmetic and allows another controller to share the current transaction. `bookings.history(user_id) -> list[BookingResult]`, `create(BookingCreate, user_id) -> Booking`, `cancel(id, BookingUpdate, user_id) -> Booking`, and `delete(id, user_id) -> None` manage the authenticated user’s bookings. Controllers may call these contracts, not another controller's private helpers or HTTP endpoints.
- The booking controller owns user selection, IDs, booking date, ownership checks, and cancellation. Resolve the current user from the server-side session, never from a client-supplied user_id. Keep legacy users and booking references intact; do not assign their bookings to new accounts. Seed all four supplied CSVs once, preserving their IDs and relationships. Use versioned seed markers to upgrade older hotels/trips-only databases. Never overwrite existing records or re-import deleted seeds after that migration. Use login and account creation instead of a demo traveler selector. Seed data is initial data, not a content limit; new bookings receive UUID-based IDs and persist in SQLite.
- HTTP contracts: GET `/api/trips?city=...` → 200 TripResult array; GET `/api/bookings` → 200 BookingResult array; POST `/api/bookings` with `{trip_id}` → 201 Booking; PATCH `/api/bookings/{id}` with `{status: "cancelled"}` → 200 Booking; DELETE `/api/bookings/{id}` → 204 with no body. Invalid input → 422, missing/unowned records → 404, conflicts → 409. Errors use `{detail: ...}` (framework validation may return a detail array). No public CRUD endpoints for hotels, users, or trips are needed merely because internal CRUD exists.
- TripResult contains Trip fields plus hotel_name, city, state, nights, nightly_rate_usd, stay_price_usd. BookingResult contains Booking fields plus trip_name, check_in, check_out, hotel_name, city, nightly_rate_usd, stay_price_usd. Dates serialize as ISO strings. TripResult money and BookingResult stay_price_usd serialize as JSON numbers; BookingResult nightly_rate_usd remains a decimal string for compatibility. Booking history sorts booked_on descending, then booking_id ascending. Empty collections are `[]`.
- The View owns Vue components, UI state, form interaction, date/currency presentation, logos, artwork, and CSS. It calls relative `/api` URLs and displays the defined response fields. It must not implement persistence, reference checks, ownership rules, price calculations, or booking status transitions independently of the backend.
- Keep route handlers free of SQL and business logic. Declare response schemas and map controller errors at the HTTP boundary. Update models, controller contracts, API tests, and README together when a boundary changes. Test persistence with isolated temporary databases; never use tests to mutate the live database.


## Account contracts

- `controllers/accounts.py` owns username normalization, credential comparison, registration, and sessions. `register(AccountCreate) -> Account`; `login(Credentials, old_token?) -> (Account, token)`; `current(token) -> Account`; `logout(token) -> None`. Authentication failures raise AuthenticationError, mapped to HTTP 401. Username conflicts map to 409.
- `AccountCreate` accepts username, password, optional email; `Credentials` accepts username/password. Usernames are trimmed, lowercased, 1–50 ASCII letters/digits/underscore/dot/dash and unique case-insensitively. Passwords are 1–256 characters and are stored as salted PBKDF2 hashes using the standard library. Account responses expose user_id, username, display_name, email, never password.
- Existing user rows gain nullable username/password/email fields without changing IDs. No default passwords are assigned to seed or legacy users. New accounts receive UUID-based IDs. Old records and their references remain unchanged.
- POST `/api/accounts` → 201 Account; POST `/api/login` → 200 Account plus HttpOnly SameSite=Strict session cookie; GET `/api/account` → Account or 401; POST `/api/logout` invalidates the session and clears the cookie, returning 204. Sessions persist in SQLite with a 24-hour expiration. Local HTTP uses a non-Secure cookie; enable Secure for HTTPS deployment.
- Search and booking API routes require a session. The HTTP adapter passes its user_id to business controllers. Search records store that user_id and city in SQLite; booking ownership checks use that same user_id. Neither registration nor login reassigns existing bookings.
- Database-only account operations: find_user(username) -> User or None; save_session(token, user_id, expires_at) -> None; session_user(token, now) -> User or None; remove_session(token) -> None; record_search(search_id, user_id, city) -> None. These keep SQL out of the account and search controllers.
- The View shows account creation/login when signed out and the signed-in username/logout when signed in. It must clear account-specific results and history at logout and on an expired session. Existing CRUD tests may override the authenticated principal; account integration tests must exercise real sessions without overrides.
