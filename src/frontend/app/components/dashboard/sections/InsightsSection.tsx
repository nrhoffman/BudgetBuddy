"use client";

interface Props {
  accountType: string;
}

export default function InsightsSection({ accountType }: Props) {
  return (
    <div className="bg-white rounded shadow p-6">
      <h2 className="text-2xl font-semibold mb-4">Insights</h2>
      <p className="text-gray-600">
        Balance over time graph for {accountType} accounts will go here.
      </p>
    </div>
  );
}