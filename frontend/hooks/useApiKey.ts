"use client";

import  { useEffect, useState } from "react";

export function useApiKey() {
    const [apiKey, setApiKeyState] = useState<string | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem("api_key");
        if (stored) setApiKeyState(stored);
    }, []);

    const setApiKey = (key: string) => {
        localStorage.setItem("api_key", key);
        setApiKeyState(key);
    }

    const clearApiKey = () => {
        localStorage.removeItem("api_key");
        setApiKeyState(null);
    }

    return { apiKey, setApiKey, clearApiKey };
}