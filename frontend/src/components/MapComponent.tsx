'use client'

import { useEffect, useRef, useCallback } from 'react'
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Tooltip,
  useMapEvents,
} from 'react-leaflet'
import L from 'leaflet'
import type { MapProps } from './Map'

// ── Fix Leaflet default icon issue (Next.js / webpack) ────────────────────
function fixLeafletIcons() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconRetinaUrl:
      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    shadowUrl:
      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  })
}

// ── Custom emoji div icons ─────────────────────────────────────────────────
function createEmojiIcon(emoji: string): L.DivIcon {
  return L.divIcon({
    className: 'custom-emoji-marker',
    html: `<span style="font-size:2rem;line-height:1;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.6))">${emoji}</span>`,
    iconSize: [36, 36],
    iconAnchor: [18, 34],
    tooltipAnchor: [0, -36],
    popupAnchor: [0, -36],
  })
}

const startIcon = createEmojiIcon('🚢')
const endIcon = createEmojiIcon('📍')

// ── Click handler (inner component to use map events) ─────────────────────
function ClickHandler({
  onPointSelect,
}: {
  onPointSelect: (lat: number, lng: number) => void
}) {
  useMapEvents({
    click(e) {
      onPointSelect(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

// ── Main map component ─────────────────────────────────────────────────────
export default function MapComponent({
  startPoint,
  endPoint,
  route,
  onPointSelect,
}: MapProps) {
  const iconsFixed = useRef(false)

  useEffect(() => {
    if (!iconsFixed.current) {
      fixLeafletIcons()
      iconsFixed.current = true
    }
  }, [])

  const handleClick = useCallback(
    (lat: number, lng: number) => {
      onPointSelect(lat, lng)
    },
    [onPointSelect],
  )

  const routePositions: [number, number][] =
    route?.route.waypoints.map((wp) => [wp.lat, wp.lon]) ?? []

  return (
    <MapContainer
      center={[10.5, 105.5]}
      zoom={8}
      className="w-full h-full"
      style={{ background: '#0c4a6e' }}
      zoomControl={true}
    >
      {/* ── Tile layer ── */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={18}
      />

      {/* ── Click handler ── */}
      <ClickHandler onPointSelect={handleClick} />

      {/* ── Start marker ── */}
      {startPoint && (
        <Marker
          position={[startPoint.lat, startPoint.lon]}
          icon={startIcon}
        >
          <Tooltip
            direction="top"
            offset={[0, -34]}
            permanent={false}
            className="!bg-ocean-900/90 !text-ocean-100 !border-ocean-500/30 !text-xs"
          >
            <span className="font-semibold text-teal-300">Departure</span>
            <br />
            {startPoint.lat.toFixed(5)}, {startPoint.lon.toFixed(5)}
          </Tooltip>
        </Marker>
      )}

      {/* ── End marker ── */}
      {endPoint && (
        <Marker
          position={[endPoint.lat, endPoint.lon]}
          icon={endIcon}
        >
          <Tooltip
            direction="top"
            offset={[0, -34]}
            permanent={false}
            className="!bg-ocean-900/90 !text-ocean-100 !border-ocean-500/30 !text-xs"
          >
            <span className="font-semibold text-sky-300">Destination</span>
            <br />
            {endPoint.lat.toFixed(5)}, {endPoint.lon.toFixed(5)}
          </Tooltip>
        </Marker>
      )}

      {/* ── Route polyline ── */}
      {routePositions.length > 1 && (
        <>
          {/* Shadow / glow */}
          <Polyline
            positions={routePositions}
            pathOptions={{
              color: '#0ea5e9',
              weight: 8,
              opacity: 0.15,
            }}
          />
          {/* Main route line */}
          <Polyline
            positions={routePositions}
            pathOptions={{
              color: '#38bdf8',
              weight: 4,
              opacity: 0.9,
              dashArray: undefined,
            }}
          />
          {/* Animated dashes overlay */}
          <Polyline
            positions={routePositions}
            pathOptions={{
              color: '#ffffff',
              weight: 2,
              opacity: 0.4,
              dashArray: '8 14',
            }}
          />
        </>
      )}
    </MapContainer>
  )
}
