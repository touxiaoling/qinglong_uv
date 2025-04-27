import axios from 'axios'

const api = axios.create({
  baseURL: '/api',  // 生产环境使用相对路径
})

export default {
  async getHello() {
    const response = await api.get('/hello')
    return response.data
  }
}