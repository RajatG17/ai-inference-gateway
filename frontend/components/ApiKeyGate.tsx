"use client";

import { useState } from "react";
import { useApiKey } from "@/hooks/useApiKey";

export default function ApiKeyGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const { apiKey, setApiKey } = useApiKey();
  const [input, setInput] = useState("");

  if (!apiKey) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="bg-white p-6 rounded-xl shadow-md w-96">
          <h2 className="text-lg font-semibold mb-4">
            Enter API Key
          </h2>

          <input
            type="password"
            placeholder="sk-..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full border p-2 rounded mb-4"
          />

          <button
            onClick={() => setApiKey(input)}
            className="w-full bg-black text-white py-2 rounded hover:bg-gray-800"
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}