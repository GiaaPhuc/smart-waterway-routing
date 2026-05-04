'use client'

import dynamic from 'next/dynamic'
import type { GeoPoint, RouteResult } from '@/app/page'

export interface MapProps {
  startPoint: GeoPoint | null
  endPoint: GeoPoint | null
  route: RouteResult | null
  onPointSelect: (lat: number, lng: number) => void
}

// Dynamically import the actual Leaflet map with SSR disabled
const MapComponent = dynamic(() => import('./MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-ocean-950">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-2 border-ocean-400/40 border-t-ocean-300 rounded-full animate-spin" />
        <p className="text-ocean-400 text-sm">Loading map…</p>
      </div>
    </div>
  ),
})

export default function Map(props: MapProps) {
  return <MapComponent {...props} />
}
