<script setup>
import { ref, watch } from 'vue'
import HotelMap from './HotelMap.vue'

const emit = defineEmits(['session-expired'])
const postcode = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

watch(postcode, () => {
  result.value = null
  error.value = ''
})

async function lookup() {
  if (loading.value) return
  loading.value = true
  result.value = null
  error.value = ''
  try {
    const response = await fetch('/api/hotels?' + new URLSearchParams({ postcode: postcode.value }))
    const data = await response.json().catch(() => null)
    if (response.status === 401) {
      emit('session-expired')
      return
    }
    if (!response.ok) {
      error.value = typeof data?.detail === 'string'
        ? data.detail
        : response.status === 422
          ? 'Enter exactly five digits for a U.S. ZIP code.'
          : 'Unable to look up this ZIP. Please try again.'
    } else if (data) {
      result.value = data
    } else {
      error.value = 'Unable to read the location response. Please try again.'
    }
  } catch {
    error.value = 'Unable to reach the server. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="zip-demo" aria-labelledby="zip-demo-title">
    <h2 id="zip-demo-title">Hotels near a U.S. ZIP code</h2>
    <form @submit.prevent="lookup">
      <label for="zip-postcode">U.S. ZIP code</label>
      <input id="zip-postcode" v-model="postcode" type="text" inputmode="numeric"
        autocomplete="postal-code" pattern="[0-9]{5}" minlength="5" maxlength="5"
        required :disabled="loading" aria-describedby="zip-format" />
      <p id="zip-format">Enter a five-digit ZIP code, including any leading zeros.</p>
      <button class="primary" type="submit" :disabled="loading">Find nearby hotels</button>
    </form>
    <div aria-live="polite" :aria-busy="loading">
      <p v-if="loading" role="status">Finding hotels near ZIP {{ postcode }}…</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <template v-if="result">
        <h3>Hotels within 5 km of the resolved ZIP location</h3>
        <dl>
          <div><dt>Postcode</dt><dd>{{ result.location.postcode }}</dd></div>
          <div v-if="result.location.locality"><dt>Locality</dt><dd>{{ result.location.locality }}</dd></div>
          <div><dt>Latitude</dt><dd>{{ result.location.latitude }}</dd></div>
          <div><dt>Longitude</dt><dd>{{ result.location.longitude }}</dd></div>
        </dl>
        <p>The search circle is centered on this resolved location. Hotel listings do not indicate availability, pricing, or bookability.</p>
        <HotelMap :result="result" />
        <p v-if="!result.hotels.length">No hotels found within 5 km of this location.</p>
        <ol v-else>
          <li v-for="hotel in result.hotels" :key="hotel.provider_place_id">
            <strong class="hotel-name">{{ hotel.name || 'Unnamed hotel' }}</strong>
            <p v-if="hotel.address">{{ hotel.address }}</p>
          </li>
        </ol>
        <p>Location data: <a href="https://www.geoapify.com/">Geoapify</a> / <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a></p>
      </template>
    </div>
  </section>
</template>

<style scoped>
.zip-demo {
  max-width: 1120px;
  margin: 24px auto;
  padding: 24px;
  border: 1px solid #d9e2e0;
  border-radius: 16px;
  background: #fff;
}
h2 { margin-bottom: 16px; }
.hotel-name { font-size: 1.25em; line-height: 1.3; font-weight: 700; }
form { display: grid; gap: 12px; justify-items: start; }
input {
  max-width: 100%;
  border: 2px solid #205bd8;
  border-radius: 8px;
  padding: 10px 12px;
}
#zip-format { margin: 0; }
p, dl { margin-top: 16px; }
dl { display: grid; gap: 12px; }
dl > div { display: flex; flex-wrap: wrap; gap: 8px 16px; }
dt { min-width: 90px; font-weight: 600; }
dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 1168px) {
  .zip-demo { margin-inline: 24px; }
}
</style>
