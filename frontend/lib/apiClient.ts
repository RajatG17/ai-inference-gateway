import axios from "axios";

const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
});

apiClient.interceptors.request.use((config) => {
    const apiKey = localStorage.getItem("api_key");
    if (apiKey) {
        config.headers["Authorization"] = `Bearer ${apiKey}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem("api_key");
            window.location.reload();
        }
        return Promise.reject(error);
    }
);

export default apiClient;