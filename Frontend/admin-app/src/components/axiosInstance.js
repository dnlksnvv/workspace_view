import axios from 'axios';

// Существующий экземпляр для Python сервера
const axiosInstance = axios.create({
  baseURL: 'http://192.168.0.188:8000/api',
  withCredentials: true,
});

const axiosGoService = axios.create({
  baseURL: 'http://192.168.0.188:8001',  // URL Go сервера
  withCredentials: true,
});

export default axiosInstance;
export { axiosGoService };