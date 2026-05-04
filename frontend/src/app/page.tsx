'use client'

import { useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import axios from 'axios'
import SearchForm from '@/components/SearchForm'
import ETADisplay from '@/components/ETADisplay'
import { Anchor } from 'lucide-react'

const Map = dynamic(() => import('@/components/Map'), { ssr: false })

// ── Types ──────────────────────────────────────────────────────────────────
export interface GeoPoint {
  lat: number
  lon: number
  label: string
}

export interface RouteResult {
  route: {
    waypoints: Array<{ lat: number; lon: number }>
    total_distance_km: number
    segments: number
  }
  eta: {
    minutes: number
    hours: number
    arrival_time: string
  }
}

export interface VesselSettings {
  vessel_type: number
  speed_knots: number
  algorithm: string
}

// ── Component ──────────────────────────────────────────────────────────────
export default function HomePage() {
  const [startPoint, setStartPoint] = useState<GeoPoint | null>(null)
  const [endPoint, setEndPoint] = useState<GeoPoint | null>(null)
  const [route, setRoute] = useState<RouteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [clickCount, setClickCount] = useState(0)

  // Click logic: first click = start, second click = end,
  // any further click restarts the cycle (clears both and sets new start)
  const handlePointSelect = useCallback(
    (lat: number, lng: number) => {
      const label = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      const point: GeoPoint = { lat, lon: lng, label }

      if (!startPoint || (startPoint && endPoint)) {
        // No start yet, OR both already set → restart cycle
        setStartPoint(point)
        setEndPoint(null)
        setRoute(null)
        setError(null)
        setClickCount(1)
      } else {
        // Start is set but end is not → set end
        setEndPoint(point)
        setClickCount(2)
      }
    },
    [startPoint, endPoint],
  )

  const handleSubmit = useCallback(
    async (settings: VesselSettings) => {
      if (!startPoint || !endPoint) return

      setLoading(true)
      setError(null)
      setRoute(null)

      try {
        const response = await axios.post<RouteResult>('/api/route', {
          start_lat: startPoint.lat,
          start_lon: startPoint.lon,
          end_lat: endPoint.lat,
          end_lon: endPoint.lon,
          vessel_type: settings.vessel_type,
          speed_knots: settings.speed_knots,
          algorithm: settings.algorithm,
        })
        setRoute(response.data)
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const msg =
            err.response?.data?.detail ||
            err.response?.data?.message ||
            err.message
          setError(`Route calculation failed: ${msg}`)
        } else {
          setError('An unexpected error occurred. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    },
    [startPoint, endPoint],
  )

  const handleClear = useCallback(() => {
    setStartPoint(null)
    setEndPoint(null)
    setRoute(null)
    setError(null)
    setClickCount(0)
  }, [])

  return (
    <main className="flex h-screen w-full overflow-hidden">
      {/* ── Left control panel ── */}
      <aside className="w-[400px] shrink-0 h-full overflow-y-auto flex flex-col glass-panel z-10">
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-ocean-700/40">
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-xl bg-ocean-500/20 border border-ocean-400/30">
              <Anchor className="w-5 h-5 text-ocean-300" />
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text leading-tight">
                Smart Waterway
              </h1>
              <p className="text-[10px] text-ocean-400 uppercase tracking-widest font-medium">
                Routing System
              </p>
            </div>
          </div>
          <p className="text-xs text-ocean-300/70 mt-2 leading-relaxed">
            Intelligent vessel navigation for the Mekong Delta network
          </p>
        </div>

        {/* Search form */}
        <div className="px-4 py-4 flex-1 flex flex-col gap-3">
          <SearchForm
            startPoint={startPoint}
            endPoint={endPoint}
            onSubmit={handleSubmit}
            onClear={handleClear}
            loading={loading}
          />

          {/* Error state */}
          {error && (
            <div className="animate-fade-in rounded-xl p-3 bg-red-950/60 border border-red-500/30 text-red-300 text-xs leading-relaxed">
              <span className="font-semibold text-red-400">Error: </span>
              {error}
            </div>
          )}

          {/* ETA / route info */}
          <ETADisplay route={route} loading={loading} />
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-ocean-700/40 text-center">
          <p className="text-[10px] text-ocean-500">
            © 2024 Smart Waterway Routing · Mekong Delta
          </p>
        </div>
      </aside>

      {/* ── Right map panel ── */}
      <div className="flex-1 h-full relative">
        <Map
          startPoint={startPoint}
          endPoint={endPoint}
          route={route}
          onPointSelect={handlePointSelect}
        />

        {/* Click-mode hint badge */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] pointer-events-none">
          <div className="glass-card rounded-full px-4 py-1.5 text-xs text-ocean-200 font-medium shadow-lg">
            {!startPoint
              ? '🚢 Click to set departure point'
              : !endPoint
                ? '📍 Click to set destination'
                : '✅ Points set — find your route!'}
          </div>
        </div>
      </div>
    </main>
  )
}
