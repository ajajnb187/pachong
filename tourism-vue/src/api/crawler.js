import axios from 'axios'
import { ElMessage } from 'element-plus'

// 爬虫服务 - /api/crawler/* 路径
const crawlerRequest = axios.create({
  baseURL: '/crawler',
  timeout: 120000
})

// 爬虫服务 - /api/* 其他路径（datasource, scenic, admin, system）
const flaskRequest = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 120000
})

// 响应拦截器
const responseInterceptor = (response) => {
  const res = response.data
  if (res.code !== 200) {
    ElMessage.error(res.msg || '请求失败')
    return Promise.reject(new Error(res.msg || 'Error'))
  }
  return res
}

const errorInterceptor = (error) => {
  console.error('爬虫服务错误:', error)
  ElMessage.error(error.message || '系统异常')
  return Promise.reject(error)
}

crawlerRequest.interceptors.response.use(responseInterceptor, errorInterceptor)
flaskRequest.interceptors.response.use(responseInterceptor, errorInterceptor)

// 启动爬取任务
export const startCrawlTaskAPI = (data) => {
  return crawlerRequest({
    url: '/start',
    method: 'post',
    data
  })
}

// 查询任务状态
export const getTaskStatusAPI = (taskId) => {
  return crawlerRequest({
    url: `/status/${taskId}`,
    method: 'get'
  })
}

// 查询任务列表
export const getTaskListAPI = (params) => {
  return crawlerRequest({
    url: '/tasks',
    method: 'get',
    params
  })
}

// 停止任务
export const stopTaskAPI = (data) => {
  return flaskRequest({
    url: '/crawler/task/stop',
    method: 'post',
    data
  })
}

// 删除任务
export const deleteTaskAPI = (taskId) => {
  return crawlerRequest({
    url: `/task/${taskId}`,
    method: 'delete'
  })
}

// 获取数据源列表
export const getDataSourceListAPI = () => {
  return flaskRequest({
    url: '/datasource/list',
    method: 'get'
  })
}

// 管理员一键爬取福州所有景区
export const adminCrawlFuzhouAPI = (data) => {
  return flaskRequest({
    url: '/admin/crawl/fuzhou',
    method: 'post',
    data
  })
}

// 获取系统状态
export const getSystemStatusAPI = () => {
  return flaskRequest({
    url: '/system/status',
    method: 'get'
  })
}
