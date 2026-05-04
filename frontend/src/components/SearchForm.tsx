'use client'

import { useState } from 'react'
import { MapPin, Navigation, Settings2, Trash2, Route } from 'lucide-react'
import clsx from 'clsx'
import type { GeoPoint, VesselSettings } from '@/app/page'

interface SearchFormProps {
  startPoint: GeoPoint | null
  endPoint: GeoPoint | null
  onSubmit: (settings: VesselSettings) => void
  onClear: () => void
  loading: boolean
}

const VESSEL_TYPES = [
  { label: 'Small Vessel', value: 0, emoji: '⛵' },
  { label: 'Medium Vessel', value: 1, emoji: '🚤' },
  { label: 'Large Vessel', value: 2, emoji: '🚢' },
] as const

const ALGORITHMS = [
  { label: 'A* (Fastest)', value: 'astar' },
  { label: 'Dijkstra (Optimal)', value: 'dijkstra' },
] as const

export default function SearchForm({
  startPoint,
  endPoint,
  onSubmit,
  onClear,
  loading,
}: SearchFormProps) {
  const [vesselType, setVesselType] = useState<number>(0)
  const [speedKnots, setSpeedKnots] = useState<number>(8)
  const [algorithm, setAlgorithm] = useState<string>('astar')

  const canSubmit = !!startPoint && !!endPoint && !loading

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    onSubmit({ vessel_type: vesselType, speed_knots: speedKnots, algorithm })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {/* Instructions */}
      <div className="glass-card rounded-xl p-3 text-xs text-ocean-300 leading-relaxed">
        <p className="font-semibold text-ocean-200 mb-1">How to use</p>
        <ol className="list-decimal list-inside space-y-0.5 text-ocean-300/80">
          <li>Click the map to set your departure point</li>
          <li>Click again to set your destination</li>
          <li>Configure vessel settings below</li>
          <li>Press &ldquo;Find Route&rdquo; to calculate</li>
        </ol>
      </div>

      {/* Points display */}
      <div className="flex flex-col gap-2">
        <PointBadge
          icon={<Navigation className="w-3.5 h-3.5 text-teal-400" />}
          label="Departure"
          point={startPoint}
          color="teal"
        />
        <PointBadge
          icon={<MapPin className="w-3.5 h-3.5 text-sky-400" />}
          label="Destination"
          point={endPoint}
          color="sky"
        />
      </div>

      {/* Vessel settings */}
      <div className="glass-card rounded-xl p-3 flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-0.5">
          <Settings2 className="w-3.5 h-3.5 text-ocean-400" />
          <span className="text-xs font-semibold text-ocean-200 uppercase tracking-wide">
            Vessel Settings
          </span>
        </div>

        {/* Vessel type */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] text-ocean-400 font-medium">
            Vessel Type
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {VESSEL_TYPES.map((vt) => (
              <button
                key={vt.value}
                type="button"
                onClick={() => setVesselType(vt.value)}
                className={clsx(
                  'flex flex-col items-center gap-1 py-2 px-1 rounded-lg border text-center transition-all duration-200 cursor-pointer',
                  vesselType === vt.value
                    ? 'bg-ocean-500/30 border-ocean-400/60 text-ocean-100 shadow-[0_0_12px_rgba(14,165,233,0.2)]'
                    : 'bg-ocean-900/40 border-ocean-700/30 text-ocean-400 hover:border-ocean-500/40 hover:text-ocean-300',
                )}
              >
                <span className="text-base">{vt.emoji}</span>
                <span className="text-[10px] font-medium leading-tight">
                  {vt.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Speed */}
        <div className="flex flex-col gap-1.5">
          <label className="flex items-center justify-between text-[11px] text-ocean-400 font-medium">
            <span>Speed</span>
            <span className="text-ocean-200 font-bold text-xs">
              {speedKnots} knots
            </span>
          </label>
          <input
            type="range"
            min={3}
            max={15}
            step={0.5}
            value={speedKnots}
            onChange={(e) => setSpeedKnots(parseFloat(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer
                       bg-ocean-800
                       [&::-webkit-slider-thumb]:appearance-none
                       [&::-webkit-slider-thumb]:w-4
                       [&::-webkit-slider-thumb]:h-4
                       [&::-webkit-slider-thumb]:rounded-full
                       [&::-webkit-slider-thumb]:bg-ocean-400
                       [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(14,165,233,0.5)]
                       [&::-webkit-slider-thumb]:cursor-pointer
                       [&::-webkit-slider-thumb]:border-2
                       [&::-webkit-slider-thumb]:border-ocean-200"
          />
          <div className="flex justify-between text-[10px] text-ocean-500">
            <span>3 kn</span>
            <span>9 kn</span>
            <span>15 kn</span>
          </div>
        </div>

        {/* Algorithm */}
        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] text-ocean-400 font-medium">
            Pathfinding Algorithm
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {ALGORITHMS.map((alg) => (
              <button
                key={alg.value}
                type="button"
                onClick={() => setAlgorithm(alg.value)}
                className={clsx(
                  'py-2 px-3 rounded-lg border text-[11px] font-medium transition-all duration-200 cursor-pointer',
                  algorithm === alg.value
                    ? 'bg-teal-500/20 border-teal-400/50 text-teal-200 shadow-[0_0_10px_rgba(20,184,166,0.15)]'
                    : 'bg-ocean-900/40 border-ocean-700/30 text-ocean-400 hover:border-ocean-500/40 hover:text-ocean-300',
                )}
              >
                {alg.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!canSubmit}
          className={clsx(
            'flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-sm transition-all duration-200',
            canSubmit
              ? 'bg-gradient-to-r from-ocean-500 to-teal-500 text-white shadow-[0_4px_20px_rgba(14,165,233,0.35)] hover:shadow-[0_6px_24px_rgba(14,165,233,0.5)] hover:scale-[1.02] active:scale-[0.98]'
              : 'bg-ocean-800/50 text-ocean-600 cursor-not-allowed border border-ocean-700/30',
          )}
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>Calculating…</span>
            </>
          ) : (
            <>
              <Route className="w-4 h-4" />
              <span>Find Route</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onClear}
          disabled={loading}
          title="Clear all points"
          className={clsx(
            'p-2.5 rounded-xl border transition-all duration-200',
            loading
              ? 'border-ocean-700/30 text-ocean-700 cursor-not-allowed'
              : 'border-ocean-600/40 text-ocean-400 hover:border-red-500/50 hover:text-red-400 hover:bg-red-950/20',
          )}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </form>
  )
}

// ── Sub-component: coordinate badge ───────────────────────────────────────
function PointBadge({
  icon,
  label,
  point,
  color,
}: {
  icon: React.ReactNode
  label: string
  point: GeoPoint | null
  color: 'teal' | 'sky'
}) {
  return (
    <div
      className={clsx(
        'flex items-center gap-2.5 rounded-xl px-3 py-2 border transition-all duration-300',
        point
          ? color === 'teal'
            ? 'bg-teal-950/40 border-teal-500/30'
            : 'bg-sky-950/40 border-sky-500/30'
          : 'bg-ocean-900/30 border-ocean-700/20',
      )}
    >
      <div
        className={clsx(
          'p-1.5 rounded-lg shrink-0',
          point
            ? color === 'teal'
              ? 'bg-teal-500/20'
              : 'bg-sky-500/20'
            : 'bg-ocean-800/50',
        )}
      >
        {icon}
      </div>
      <div className="flex flex-col min-w-0">
        <span
          className={clsx(
            'text-[10px] font-semibold uppercase tracking-wider',
            point
              ? color === 'teal'
                ? 'text-teal-400'
                : 'text-sky-400'
              : 'text-ocean-500',
          )}
        >
          {label}
        </span>
        {point ? (
          <span className="text-xs text-ocean-200 font-mono truncate">
            {point.lat.toFixed(5)}, {point.lon.toFixed(5)}
          </span>
        ) : (
          <span className="text-xs text-ocean-600 italic">Not set</span>
        )}
      </div>
      {point && (
        <div
          className={clsx(
            'ml-auto w-2 h-2 rounded-full shrink-0 animate-pulse',
            color === 'teal' ? 'bg-teal-400' : 'bg-sky-400',
          )}
        />
      )}
    </div>
  )
}
