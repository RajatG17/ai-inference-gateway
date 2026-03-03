import apiClient from "./apiClient";

export async function predict(payload: any) {
    const response = await apiClient.post("/v1/predict", payload);
    return response.data;
}