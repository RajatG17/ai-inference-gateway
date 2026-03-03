"use client";

import { useState } from "react";
import { usePredict } from "@/hooks/usePredict";
import ResponseCard from "./ResponseCard";
import { PredictResponse } from "@/types/prediction";

export default function PromptForm() {
  const { predict, loading, error } = usePredict();

  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("gpt-4");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(200);
  const [response, setResponse] = useState<PredictResponse | null>(null);

  const handleSubmit = async () => {
    const result = await predict({
      prompt,
      model,
      temperature,
      max_tokens: maxTokens,
      cache_bypass: false,
    });

    if (result) setResponse(result);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl shadow-md space-y-4">
        <textarea
          placeholder="Enter your prompt..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          className="w-full border p-2 rounded"
        />

        <div className="grid grid-cols-3 gap-4">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="border p-2 rounded"
          >
            <option value="gpt-4">gpt-4o</option>
            <option value="gemini-3-flash-preview">gemini-3</option>
            <option value="local">local</option>
          </select>

          <input
            type="number"
            value={temperature}
            step="0.1"
            min="0"
            max="2"
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="border p-2 rounded"
          />

          <input
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            className="border p-2 rounded"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate"}
        </button>

        {error && (
          <div className="text-red-500 text-sm">
            {error}
          </div>
        )}
      </div>

      {response && <ResponseCard data={response} />}
    </div>
  );
}