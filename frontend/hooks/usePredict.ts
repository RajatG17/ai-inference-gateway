"use client";

import {useState} from "react";
import apiClient from "@/lib/apiClient";
import { PredictResponse } from "@/types/prediction";

export function usePredict() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const predict = async (payload: any): Promise<PredictResponse | null> => {
        try {
            setLoading(true);
            setError(null);

            const res = await apiClient.post("/v1/predict", payload);
            return res.data;
        } catch(err: any) {
            setError(err.response?.data?.detail || "Unexpected error");
            return null;
        } finally {
            setLoading(false);
        }
    };

    return { predict, loading, error };
}