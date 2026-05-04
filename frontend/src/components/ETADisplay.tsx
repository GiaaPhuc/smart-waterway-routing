'use client'

import { Navigation, Clock, Anchor, MapPin, Route, Gauge } from 'lucide-react'
import clsx from 'clsx'
import type { RouteResult } from '@/app/page'

interface ETADisplayProps {
  route: RouteResult | null
  loading: boolean
}

export default function ETADisplay({ route, loading }: ETADisplayProps) {
  if (loading) {
    return (
      <div className="glass-card rounded-xl p-5 flex flex-col items-center gap-3 animate-fade-in">
        <div className="w-8 h-8 border-2 border-ocean-500/40 border-t-ocean-300 rounded-full animate-spin" />
        <p className="text-xs text-ocean-400">Computing optimal route…</p>
      </div>
    )
  }

  if (!route) {
    return (
      <div className="glass-card rounded-xl p-5 flex flex-col items-center gap-3 text-center">
        <div className="p-3 rounded-2xl bg-ocean-800/50 border border-ocean-600/20">
          <Navigation className="w-6 h-6 text-ocean-500" />
        </div>
        <div>
          <p className="text-sm font-medium text-ocean-400">No route yet</p>
          <p className="text-[11px] text-ocean-600 mt-0.5">
            Route information will appear here
          </p>
        </div>
        <div className="w-full h-px bg-ocean-700/30" />
        <div className="grid grid-cols-2 gap-2 w-full opacity-40">
          <Skeleton />
          <Skeleton />
          <Skeleton wide />
        </div>
      </div>
    )
  }

  const { route: r, eta } = route
  // eta.minutes is the total travel time in minutes (float from API)
  const totalMinutes = Math.round(eta.minutes)
  const displayHours = Math.floor(totalMinutes / 60)
  const displayMins = totalMinutes % 60

  return (
    <div className="flex flex-col gap-3 animate-fade-in">
      {/* Distance hero */}
      <div className="glass-card rounded-xl p-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-ocean-500/5 to-teal-500/5 pointer-events-none" />
        <p className="text-[10px] text-ocean-400 uppercase tracking-widest font-semibold mb-1">
          Total Distance
        </p>
        <p className="text-3xl font-bold gradient-text">
          {r.total_distance_km.toFixed(1)}
        </p>
        <p className="text-xs text-ocean-400 font-medium">kilometres</p>
        {/* Route badge */}
        <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-ocean-800/60 border border-ocean-600/30 text-[10px] text-ocean-300">
          <Route className="w-3 h-3" />
          {r.segments} segments
        </div>
      </div>

      {/* ETA card */}
      <div className="glass-card rounded-xl p-4 flex flex-col gap-3">
        <div className="flex items-center gap-2 border-b border-ocean-700/30 pb-2">
          <Clock className="w-4 h-4 text-teal-400" />
          <span className="text-xs font-semibold text-ocean-200 uppercase tracking-wide">
            Estimated Travel Time
          </span>
        </div>

        {/* Time display */}
        <div className="flex items-end justify-center gap-3">
          {displayHours > 0 && (
            <TimeUnit value={displayHours} unit="h" accent="teal" />
          )}
          <TimeUnit value={displayMins} unit="min" accent="sky" />
        </div>

        {/* Total minutes pill */}
        <div className="text-center">
          <span className="text-[10px] text-ocean-500">
            ≈ {totalMinutes} minutes total
          </span>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-2">
        <InfoCard
          icon={<Anchor className="w-3.5 h-3.5 text-ocean-400" />}
          label="Arrival"
          value={formatArrivalTime(eta.arrival_time)}
          accent="ocean"
        />
        <InfoCard
          icon={<MapPin className="w-3.5 h-3.5 text-sky-400" />}
          label="Waypoints"
          value={`${r.waypoints.length}`}
          accent="sky"
        />
        <InfoCard
          icon={<Gauge className="w-3.5 h-3.5 text-teal-400" />}
          label="Avg Speed"
          value={totalMinutes > 0 ? `${(r.total_distance_km / (totalMinutes / 60)).toFixed(1)} km/h` : '—'}
          accent="teal"
          wide
        />
      </div>
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────
function formatArrivalTime(raw: string): string {
  if (!raw) return '—'
  try {
    const d = new Date(raw)
    if (isNaN(d.getTime())) return raw
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return raw
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────
function TimeUnit({
  value,
  unit,
  accent,
}: {
  value: number
  unit: string
  accent: 'teal' | 'sky'
}) {
  return (
    <div className="flex items-end gap-1">
      <span
        className={clsx(
          'text-4xl font-bold tabular-nums',
          accent === 'teal' ? 'text-teal-300' : 'text-sky-300',
        )}
      >
        {String(value).padStart(2, '0')}
      </span>
      <span className="text-ocean-500 text-sm pb-1 font-medium">{unit}</span>
    </div>
  )
}

function InfoCard({
  icon,
  label,
  value,
  accent,
  wide,
}: {
  icon: React.ReactNode
  label: string
  value: string
  accent: 'ocean' | 'sky' | 'teal'
  wide?: boolean
}) {
  const accentBorder = {
    ocean: 'border-ocean-600/25',
    sky: 'border-sky-600/25',
    teal: 'border-teal-600/25',
  }[accent]

  return (
    <div
      className={clsx(
        'glass-card rounded-xl p-3 border',
        accentBorder,
        wide && 'col-span-2',
      )}
    >
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <span className="text-[10px] text-ocean-500 uppercase tracking-wider font-medium">
          {label}
        </span>
      </div>
      <p className="text-sm font-semibold text-ocean-100">{value}</p>
    </div>
  )
}

function Skeleton({ wide }: { wide?: boolean }) {
  return (
    <div
      className={clsx(
        'h-10 rounded-lg bg-ocean-800/50',
        wide && 'col-span-2',
      )}
    />
  )
}
