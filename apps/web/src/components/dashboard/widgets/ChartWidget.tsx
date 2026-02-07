"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { generateChartData } from "@/lib/services/geminiService";

interface ChartWidgetProps {
  content: string;
}

const ChartWidget: React.FC<ChartWidgetProps> = ({ content: topic }) => {
  const [data, setData] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!topic) {
        setData([]);
        setLoading(false);
        return;
      }

      try {
        const result = await generateChartData(topic);
        const chartData = result.labels.map((label, i) => ({
          name: label,
          value: result.data[i],
        }));
        setData(chartData);
      } catch (error) {
        console.error("[ChartWidget] Error:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [topic]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-matcha-500" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-industrial-400">
        <TrendingUp className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">No data to display</p>
      </div>
    );
  }

  return (
    <div className="h-full p-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey="name" className="text-xs" />
          <YAxis className="text-xs" />
          <Tooltip />
          <Bar dataKey="value" fill="rgb(34 197 94)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartWidget;
