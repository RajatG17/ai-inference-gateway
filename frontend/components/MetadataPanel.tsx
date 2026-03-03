import { PredictResponse } from "@/types/prediction";

export default function MetadataPanel({
  data,
}: {
  data: PredictResponse;
}) {
  return (
    <div className="text-xs text-gray-500 border-t pt-3 space-y-1">
      <div>Model: {data.model}</div>
      <div>Backend: {data.backend}</div>
      <div>Fallback Used: {data.fallback_used ? "Yes" : "No"}</div>
      <div>Cache Hit: {data.cache_hit ? "Yes" : "No"}</div>
      <div>Latency: {data.latency_ms} ms</div>
    </div>
  );
}