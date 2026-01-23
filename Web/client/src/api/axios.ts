import axios from 'axios';

const API = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
});

API.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

API.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't tried to refresh yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // Attempt to get a new access token using the HttpOnly cookie
                const res = await API.post('/refresh');
                const { accessToken } = res.data;

                // Update local storage with new token
                localStorage.setItem('accessToken', accessToken);

                // Update the authorization header for the original request
                originalRequest.headers.Authorization = `Bearer ${accessToken}`;

                // Retry the original request
                return API(originalRequest);
            } catch (refreshError) {
                // If refresh fails (e.g. cookie expired), logout user
                console.error("Session expired", refreshError);
                localStorage.removeItem('accessToken');
                localStorage.removeItem('user');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default API;
