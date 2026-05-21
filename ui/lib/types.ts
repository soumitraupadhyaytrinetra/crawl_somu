export interface Stats {
  competitors: number
  influencers: number
  events: number
  last_scraped: string | null
}

export interface Competitor {
  id: number
  name: string
  display_name: string | null
  url: string | null
  region: string | null
  type: string | null
  scraped_at: string | null
  scraped_date: string | null
  tagline: string | null
  about: string | null
  pricing_plans: string | null
  has_virtual_tryon: number
  tryon_description: string | null
  tech_hints: string | null
  categories: string | null
  sample_products: string | null
  social_links: string | null
  has_newsletter: number
  ad_tech: string | null
}

export interface Influencer {
  id: number
  handle: string
  name: string | null
  platform: string
  followers: number | null
  niche: string | null
  region: string | null
  bio: string | null
  engagement_rate: string | null
  profile_url: string | null
  scraped_at: string | null
  scraped_date: string | null
  source_url: string | null
}

export interface EventRow {
  id: number
  name: string
  event_type: string | null
  location: string | null
  region: string | null
  start_date: string | null
  end_date: string | null
  website: string | null
  organizer: string | null
  description: string | null
  target_audience: string | null
  scraped_at: string | null
  scraped_date: string | null
  source_url: string | null
}

export type Section = 'competitors' | 'influencers' | 'events'
export type Region = 'all' | 'india' | 'uae' | 'global'

export interface ScrapeJobResponse {
  job_id: string
}

export interface JobStatus {
  status: 'running' | 'done' | 'error' | 'not_found'
  message: string
}
