export interface PredictResponse {
    output: string;
    model: string;
    backend: string;
    fallback_used: boolean;
    latency_ms: number;
    cache_hit: boolean;
}