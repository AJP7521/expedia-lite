<script setup>
import { onMounted, ref } from 'vue'

const account = ref(null)
const authReady = ref(false)
const authBusy = ref(false)
const authMode = ref('login')
const username = ref('')
const password = ref('')
const email = ref('')
const authError = ref('')
const authNotice = ref('')

async function authenticate() {
  authBusy.value = true
  authError.value = ''
  authNotice.value = ''
  try {
    const body = { username: username.value, password: password.value }
    if (authMode.value === 'register') {
      await request('/accounts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, email: email.value || null }) })
      authMode.value = 'login'
      password.value = ''
      authNotice.value = 'Account created. Log in with your username and password.'
    } else {
      account.value = await request('/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      password.value = ''
      await loadHistory()
    }
  } catch (error) {
    authError.value = error.message
  } finally {
    authBusy.value = false
  }
}

function clearUser() {
  account.value = null
  bookings.value = []
  trips.value = []
  searched.value = false
  notice.value = ''
  bookingError.value = ''
  pendingDelete.value = null
  city.value = ''
}

async function logout() {
  authBusy.value = true
  authError.value = ''
  try {
    await request('/logout', { method: 'POST' })
    clearUser()
    authNotice.value = 'You have been logged out.'
  } catch (error) { authError.value = error.message }
  finally { authBusy.value = false }
}

const city = ref('')
const searchedCity = ref('')
const trips = ref([])
const loading = ref(false)
const searched = ref(false)
const error = ref('')
const dateLabel = (value) => new Date(value + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
const destinations = ['Boston', 'New York', 'Philadelphia', 'Washington', 'State College']
async function explore(destination) { city.value = destination; await search() }

const dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

const bookings = ref([])
const busy = ref(false)
const historyLoading = ref(false)
const bookingError = ref('')
const notice = ref('')
const pendingDelete = ref(null)

async function request(path, options) {
  const response = await fetch('/api' + path, options)
  if (!response.ok) {
    if (response.status === 401 && account.value) clearUser()
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Check your input. Use letters, numbers, dots, dashes, or underscores for your username.')
  }
  return response.status === 204 ? null : response.json()
}

async function loadHistory() {
  bookings.value = []
  pendingDelete.value = null
  historyLoading.value = true
  bookingError.value = ''
  try {
    bookings.value = await request('/bookings')
  } catch {
    bookingError.value = 'Unable to load booking history. Please retry.'
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  try {
    const response = await fetch('/api/account')
    if (response.ok) { account.value = await response.json(); await loadHistory() }
    else if (response.status !== 401) authError.value = 'Unable to load your account. Please try logging in.'
  } catch { authError.value = 'Unable to reach the server. Please try again.' }
  finally { authReady.value = true }
})

async function changeBooking(method, bookingId, tripId) {
  if (busy.value || historyLoading.value) return
  busy.value = true
  bookingError.value = ''
  notice.value = ''
  try {
    const body = method === 'POST'
      ? { trip_id: tripId }
      : { status: 'cancelled' }
    await request('/bookings' + (bookingId ? '/' + bookingId : ''), {
      method,
      ...(method !== 'DELETE' && {
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }),
    })
    notice.value = method === 'POST' ? 'Booking confirmed. Your simulated stay is in My bookings.'
      : method === 'PATCH' ? 'Booking cancelled. The record remains in history.'
        : 'Test booking deleted.'
    await loadHistory()
  } catch {
    bookingError.value = 'Unable to confirm the change. Refresh history before trying again.'
  } finally {
    busy.value = false
  }
}

async function search() {
  if (loading.value) return
  error.value = ''
  trips.value = []
  searched.value = false
  const query = city.value.trim()
  if (!query) {
    error.value = 'Enter a city to search.'
    return
  }
  loading.value = true
  searchedCity.value = query
  try {
    trips.value = await request('/trips?' + new URLSearchParams({ city: query }))
    searched.value = true
  } catch {
    error.value = 'Unable to load trips. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <header class="site-header">
    <a class="brand" href="#" aria-label="Expedia Lite home"><img src="/logo.svg" alt="" width="40" height="40" />Expedia<span>Lite</span></a>
    <nav v-if="account" aria-label="Main navigation"><a href="#find-stay">Find a stay</a><a href="#bookings">My bookings <span class="count">{{ bookings.length }}</span></a><span class="signed-in">{{ account.username }}</span><button class="secondary" :disabled="authBusy || busy || loading || historyLoading" @click="logout">Log out</button></nav>
  </header>
  <main v-if="!account" class="account-page">
    <section class="account-panel" aria-labelledby="account-title">
      <p class="eyebrow">YOUR NEXT CHAPTER STARTS HERE</p>
      <h1 id="account-title">{{ authMode === 'register' ? 'Create your account' : 'Welcome back' }}</h1>
      <p>Sign in to search stays and keep your bookings together.</p>
      <p v-if="!authReady" role="status">Checking your session…</p>
      <form v-else @submit.prevent="authenticate">
        <label for="username">Username</label><input id="username" v-model="username" autocomplete="username" required maxlength="50" :disabled="authBusy" />
        <label for="password">Password</label><input id="password" v-model="password" type="password" :autocomplete="authMode === 'register' ? 'new-password' : 'current-password'" required maxlength="256" :disabled="authBusy" />
        <template v-if="authMode === 'register'"><label for="email">Email (optional)</label><input id="email" v-model="email" type="email" autocomplete="email" maxlength="254" :disabled="authBusy" /></template>
        <p v-if="authError" class="error" role="alert">{{ authError }}</p><p v-if="authNotice" class="success" role="status">{{ authNotice }}</p>
        <button class="primary" type="submit" :disabled="authBusy">{{ authBusy ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Log in' }}</button>
        <button class="text-button" type="button" :disabled="authBusy" @click="authMode = authMode === 'login' ? 'register' : 'login'; authError = ''; authNotice = ''; password = ''">{{ authMode === 'login' ? 'New here? Create an account' : 'Already have an account? Log in' }}</button>
      </form>
      <p class="account-note">Simulated stays. No real reservations or payments.</p>
    </section>
  </main>
  <main v-else>
    <p v-if="authError" class="error" role="alert">{{ authError }}</p>
    <section class="hero" id="find-stay" aria-labelledby="hero-title">
      <div class="hero-copy"><p class="eyebrow">A LITTLE ESCAPE. A FRESH PERSPECTIVE.</p><h1 id="hero-title">Your next getaway<br />starts here.</h1><p>Discover a new city. Find a place to call home.<br class="desktop-break" /> Make room for something different.</p><span class="hero-note">Thoughtfully simple travel planning</span></div>
      <div class="hero-art" aria-hidden="true"><div class="sun"></div><div class="hill hill-back"></div><div class="hotel"><div class="hotel-top"></div><div class="windows"><i v-for="n in 12" :key="n"></i></div><div class="door"></div></div><div class="hill hill-front"></div><div class="art-label">A change of scenery awaits ↗</div></div>
    </section>
    <form class="search-panel" @submit.prevent="search">
      <div class="search-field"><label for="city">Where would you like to go?</label><div class="input-wrap"><span aria-hidden="true">⌕</span><input id="city" v-model="city" placeholder="Enter a destination city" :disabled="loading" /></div></div>
      <button class="primary search-button" type="submit" :disabled="loading">{{ loading ? 'Searching…' : 'Search stays' }} <span aria-hidden="true">→</span></button>
    </form>
    <div class="destination-shortcuts"><span>Explore a city</span><button v-for="destination in destinations" :key="destination" class="chip" :disabled="loading" @click="explore(destination)">{{ destination }}</button></div>
    <p class="simulation-note"><span class="small-dot"></span> A travel sandbox. All stays are fictional; bookings are simulated and no payments are made.</p>
    <div class="feedback" aria-live="polite"><p v-if="notice" class="success" role="status">✓ {{ notice }} <a href="#bookings">View my bookings →</a></p><p v-if="bookingError" role="alert" class="error">{{ bookingError }}</p></div>
    <section class="stays-section" aria-labelledby="stays-title">
      <div class="section-heading"><div><p class="eyebrow">FIND YOUR NEXT CHAPTER</p><h2 id="stays-title">{{ searched ? 'Stays in ' + searchedCity : 'A great stay is a search away' }}</h2></div><span v-if="searched && trips.length" class="muted">{{ trips.length }} stays to explore</span></div>
      <p v-if="error" role="alert" class="error">{{ error }}</p>
      <p v-if="loading" class="empty-state" role="status">Finding your next stay…</p>
      <div v-else-if="!trips.length" class="empty-state" role="status"><span class="empty-icon" aria-hidden="true">⌕</span><h3>{{ searched ? 'No stays found just yet' : 'Where will curiosity take you?' }}</h3><p>{{ searched ? 'Try another city or choose one of the destinations above.' : 'Search a city to discover hotel stays, dates, and clear upfront prices.' }}</p></div>
      <div v-else class="stay-grid">
        <article v-for="(trip, index) in trips" :key="trip.trip_id" class="stay-card">
          <div class="card-art" :class="'palette-' + index % 3" aria-hidden="true"><span class="card-city">{{ trip.city }}</span><div class="art-orbit"></div><div class="mini-building"><i v-for="n in 6" :key="n"></i></div><span class="art-caption">CITY ESCAPES</span></div>
          <div class="card-content"><p class="location">{{ trip.city }}, {{ trip.state }} <span>· {{ trip.nights }} nights</span></p><h3>{{ trip.hotel_name }}</h3><p class="trip-name">{{ trip.trip_name }}</p><div class="stay-dates"><span>{{ dateLabel(trip.check_in) }}</span><span aria-hidden="true">→</span><span>{{ dateLabel(trip.check_out) }}</span></div><div class="card-bottom"><div><span class="price">{{ dollars.format(trip.stay_price_usd) }}</span><span class="price-label">Total stay · {{ dollars.format(trip.nightly_rate_usd) }}/night</span></div><button class="primary" :disabled="busy || historyLoading" :aria-label="'Book stay at ' + trip.hotel_name + ', ' + trip.trip_name" @click="changeBooking('POST', null, trip.trip_id)">{{ busy ? 'Working…' : 'Book stay' }}</button></div></div>
        </article>
      </div>
    </section>
    <section id="bookings" class="bookings-section" aria-labelledby="history-title">
      <div class="section-heading"><div><p class="eyebrow">ALL YOUR PLANS, ONE PLACE</p><h2 id="history-title">My bookings</h2></div><button class="secondary" :disabled="busy || historyLoading" @click="loadHistory">{{ historyLoading ? 'Refreshing…' : 'Refresh history' }}</button></div>
      <p class="section-description">Your next escape, and the places you planned along the way.</p>
      <p v-if="historyLoading" role="status">Loading your bookings…</p>
      <div v-else-if="!bookings.length && !bookingError" class="empty-state"><span class="empty-icon" aria-hidden="true">▤</span><h3>Your itinerary is a blank canvas</h3><p>Find a stay you love and book it. Your plans will appear right here.</p><a class="text-link" href="#find-stay">Find your first stay →</a></div>
      <div v-if="pendingDelete" class="delete-confirmation" role="group" aria-label="Confirm deletion"><h3>Delete this booking?</h3><p>This permanently removes the record. Cancel instead if you want to keep it in your history.</p><p class="booking-id">{{ pendingDelete }}</p><button class="danger" :disabled="busy" @click="changeBooking('DELETE', pendingDelete)">Confirm delete</button><button class="secondary" :disabled="busy" @click="pendingDelete = null">Keep booking</button></div>
      <div class="booking-list"><article v-for="booking in bookings" :key="booking.booking_id" class="booking-card"><div class="booking-symbol" aria-hidden="true">▤</div><div class="booking-info"><span class="status-badge" :class="booking.status">{{ booking.status }}</span><h3>{{ booking.hotel_name }}</h3><p>{{ booking.trip_name }} · {{ dateLabel(booking.check_in) }} – {{ dateLabel(booking.check_out) }}</p><details><summary>Booking reference</summary><span class="booking-id">{{ booking.booking_id }}</span></details></div><div class="booking-summary"><strong>{{ dollars.format(booking.stay_price_usd) }}</strong><span class="price-label">Total stay</span><div class="booking-actions"><button v-if="booking.status === 'confirmed'" class="text-button" :disabled="busy || historyLoading" @click="changeBooking('PATCH', booking.booking_id)">Cancel booking</button><button class="text-button delete-link" :disabled="busy || historyLoading" @click="pendingDelete = booking.booking_id">Delete</button></div></div></article></div>
    </section>
  </main>
  <footer><a class="brand footer-brand" href="#"><img src="/logo.svg" alt="" width="28" height="28" />Expedia<span>Lite</span></a><p>Small escapes. New perspectives.</p><span>Built for exploration · Simulated bookings only</span></footer>
</template>
