import request from '@/utils/request'

export const getOverviewAPI = () => {
  return request({
    url: '/analysis/overview',
    method: 'GET'
  })
}

export const getScenicListAPI = (params) => {
  return request({
    url: '/analysis/scenic/list',
    method: 'GET',
    params
  })
}

export const getVisitorCountAPI = (params) => {
  return request({
    url: '/analysis/visitor-count',
    method: 'GET',
    params
  })
}

export const getReviewStatsAPI = (spotId) => {
  return request({
    url: '/analysis/review-stats',
    method: 'GET',
    params: { spotId }
  })
}

export const getSeasonPatternAPI = (params) => {
  return request({
    url: '/analysis/season-pattern',
    method: 'GET',
    params
  })
}

export const getScenicRankingAPI = (params) => {
  return request({
    url: '/analysis/scenic/ranking',
    method: 'GET',
    params
  })
}

export const getVisitorSourceAPI = (params) => {
  return request({
    url: '/analysis/visitor-source',
    method: 'GET',
    params
  })
}

export const getVisitorDemographicsAPI = (spotId) => {
  return request({
    url: '/analysis/visitor-demographics',
    method: 'GET',
    params: { spotId }
  })
}

export const getReviewUserCountAPI = (spotId) => {
  return request({
    url: '/analysis/review-user-count',
    method: 'GET',
    params: { spotId }
  })
}

export const getRecommendVisitTimeAPI = (params) => {
  return request({
    url: '/analysis/recommend-visit-time',
    method: 'GET',
    params
  })
}

export const getTrafficAnalysisAPI = (params) => {
  return request({
    url: '/analysis/traffic-analysis',
    method: 'GET',
    params
  })
}

export const getTrafficForecastAPI = (params) => {
  return request({
    url: '/analysis/traffic-forecast',
    method: 'GET',
    params
  })
}

export const getRatingDistributionAPI = (spotId) => {
  return request({
    url: '/analysis/rating-distribution',
    method: 'GET',
    params: { spotId }
  })
}
