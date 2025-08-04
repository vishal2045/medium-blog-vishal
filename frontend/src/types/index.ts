export interface Event {
  id: number
  device_id: string
  timestamp: string
  risk_score: number
  created_at: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface EventsResponse {
  events: Event[]
  total: number
  limit: number
  offset: number
}

export interface ECGData {
  event_id: number
  timestamp: string
  device_id: string
  csv_data: string
}

export interface DashboardStats {
  total_events: number
  high_risk_events: number
  events_today: number
  average_risk_score: number
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export interface FilterOptions {
  risk_level?: RiskLevel
  date_from?: string
  date_to?: string
  device_id?: string
}