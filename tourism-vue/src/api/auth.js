import request from '@/utils/request'

export const loginAPI = (data) => {
  return request({
    url: '/auth/login',
    method: 'POST',
    data
  })
}

export const getUserInfoAPI = () => {
  return request({
    url: '/auth/userinfo',
    method: 'GET'
  })
}

export const logoutAPI = () => {
  return request({
    url: '/auth/logout',
    method: 'POST'
  })
}
