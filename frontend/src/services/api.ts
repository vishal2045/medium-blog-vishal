import axios from 'axios'
import type { EventsResponse, ECGData, FilterOptions } from '../types'

// API base URL - will be set via environment variable in production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    
    // Handle specific error cases
    if (error.response?.status === 503) {
      throw new Error('Backend service is currently unavailable. Please try again later.')
    }
    
    if (error.response?.status >= 500) {
      throw new Error('Server error occurred. Please contact support if the problem persists.')
    }
    
    if (error.response?.status === 404) {
      throw new Error('Requested resource not found.')
    }
    
    throw error
  }
)

export const apiService = {
  // Health check
  async healthCheck(): Promise<{ status: string; database: string }> {
    const response = await api.get('/health')
    return response.data
  },

  // Get events with pagination and filtering
  async getEvents(
    limit: number = 50,
    offset: number = 0,
    filters?: FilterOptions
  ): Promise<EventsResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    })

    if (filters?.risk_level) {
      // Convert risk level to minimum risk score
      const riskScoreMap = {
        HIGH: 0.8,
        MEDIUM: 0.5,
        LOW: 0.0,
      }
      params.append('min_risk_score', riskScoreMap[filters.risk_level].toString())
    }

    const response = await api.get(`/events?${params.toString()}`)
    return response.data
  },

  // Get ECG data for a specific event
  async getEventECG(eventId: number): Promise<ECGData> {
    const response = await api.get(`/events/${eventId}/csv`)
    return response.data
  },

  // Download ECG CSV file
  async downloadECGCSV(eventId: number, filename?: string): Promise<void> {
    try {
      const ecgData = await this.getEventECG(eventId)
      
      // Create blob and download
      const blob = new Blob([ecgData.csv_data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `ecg_${eventId}_${ecgData.timestamp.replace(/:/g, '-')}.csv`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading ECG CSV:', error)
      throw error
    }
  },

  // Get dashboard statistics (mock implementation - extend backend if needed)
  async getDashboardStats(): Promise<{
    total_events: number
    high_risk_events: number
    events_today: number
    average_risk_score: number
  }> {
    // Get recent events to calculate stats
    const recentEvents = await this.getEvents(1000, 0)
    
    const today = new Date().toISOString().split('T')[0]
    const eventsToday = recentEvents.events.filter(event => 
      event.timestamp.startsWith(today)
    )
    
    const highRiskEvents = recentEvents.events.filter(event => 
      event.risk_score > 0.8
    )
    
    const averageRiskScore = recentEvents.events.length > 0
      ? recentEvents.events.reduce((sum, event) => sum + event.risk_score, 0) / recentEvents.events.length
      : 0

    return {
      total_events: recentEvents.total,
      high_risk_events: highRiskEvents.length,
      events_today: eventsToday.length,
      average_risk_score: averageRiskScore,
    }
  },
}

export default apiService