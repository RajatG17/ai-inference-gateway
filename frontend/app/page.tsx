"use client";

import ApiKeyGate from "@/components/ApiKeyGate";
import type { ReactNode } from "react";
import PromptForm from "@/components/PromptForm";

export default function Home() {
  return (
    <ApiKeyGate>
      <div className="max-w-3xl mx-auto">
        <PromptForm />
      </div>
    </ApiKeyGate>
  );
}