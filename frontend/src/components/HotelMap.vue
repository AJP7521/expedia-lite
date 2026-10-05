<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerUrl from 'leaflet/dist/images/marker-icon.png'
import markerRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps({ result: { type: Object, required: true } })
const container = ref(null)
const tileError = ref(false)
let map
let resultsLayer
let resizeObserver

const hotelIcon = L.icon({
  iconUrl: markerUrl,
  iconRetinaUrl: markerRetinaUrl,
  shadowUrl: markerShadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function drawResults() {
  if (!map) return
  resultsLayer.clearLayers()
  const { search_center: center, radius_meters: radius, location, hotels } = props.result
  const point = [center.latitude, center.longitude]
  const circle = L.circle(point, {
    radius, color: '#205bd8', weight: 2, fillOpacity: 0.08, interactive: false,
  }).addTo(resultsLayer)
  const centerLabel = document.createElement('span')
  centerLabel.textContent = `Resolved ZIP ${location.postcode} search center`
  L.circleMarker(point, {
    radius: 7, color: '#fff', weight: 2, fillColor: '#d34b21', fillOpacity: 1,
  }).bindTooltip(centerLabel).addTo(resultsLayer)

  for (const hotel of hotels) {
    // Provider text must be rendered as text, never interpreted as popup HTML.
    const popup = document.createElement('div')
    const name = document.createElement('strong')
    name.className = 'hotel-popup-name'
    name.textContent = hotel.name || 'Unnamed hotel'
    popup.append(name)
    if (hotel.address) {
      const address = document.createElement('p')
      address.textContent = hotel.address
      popup.append(address)
    }
    L.marker([hotel.latitude, hotel.longitude], {
      icon: hotelIcon, title: hotel.name || 'Unnamed hotel', alt: hotel.name || 'Unnamed hotel',
    }).bindPopup(popup).addTo(resultsLayer)
  }
  map.fitBounds(circle.getBounds(), { padding: [20, 20] })
}

onMounted(() => {
  const center = props.result.search_center
  // Initialize the projection before adding layers and measuring circle bounds.
  map = L.map(container.value, { scrollWheelZoom: false })
    .setView([center.latitude, center.longitude], 12)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).on('tileerror', () => { tileError.value = true }).addTo(map)
  resultsLayer = L.layerGroup().addTo(map)
  drawResults()
  resizeObserver = new ResizeObserver(() => map?.invalidateSize())
  resizeObserver.observe(container.value)
})

watch(() => props.result, drawResults)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
  map = null
})
</script>

<template>
  <div class="hotel-map">
    <p>Orange dot: resolved ZIP center. Blue circle: 5 km search radius. Select a hotel marker for details.</p>
    <div ref="container" class="map-canvas" role="region"
      :aria-label="`Hotels within 5 km of the resolved ZIP ${result.location.postcode} location`" />
    <p v-if="tileError" role="status">Some map tiles could not load. Hotel details remain available in the list below.</p>
  </div>
</template>

<style scoped>
.hotel-map { margin-top: 20px; }
.hotel-map :deep(.hotel-popup-name) { font-size: 1.25em; line-height: 1.3; font-weight: 700; }
.hotel-map p { margin: 12px 0; }
.map-canvas {
  height: clamp(300px, 50vh, 480px);
  width: 100%;
  border: 1px solid #d9e2e0;
  border-radius: 12px;
  isolation: isolate;
}
</style>
