import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity } from "lucide-react";
import Markdown from "react-markdown";

interface ChannelSummary {
  summary: string;
  message_count: number;
  last_active: string;
}

interface SummaryResponse {
  server_id: string;
  timestamp: string;
  channels: Record<string, ChannelSummary>;
}

export function DiscordSummary() {
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch(
	      `${import.meta.env.VITE_API_URL}/summarize/863154240319258674`,
        );
        if (!response.ok) {
          throw new Error("Failed to fetch summary");
        }
        const data = await response.json();
        setSummaryData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 rounded-md bg-red-50">
        Error: {error}
      </div>
    );
  }

  if (!summaryData || Object.keys(summaryData.channels).length === 0) {
    return (
      <div className="text-gray-500 p-4">
        No active channels found in the past week
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Discord Channel Summaries</h1>
        <div className="text-sm text-gray-500">
          Last updated: {formatDate(summaryData.timestamp)}
        </div>
      </div>

      <ScrollArea className="h-[800px] pr-4">
        <div className="space-y-4">
          {Object.entries(summaryData.channels)
            .sort(
              ([, a], [, b]) =>
                new Date(b.last_active).getTime() -
                new Date(a.last_active).getTime(),
            )
            .map(([channelName, channelData]) => (
              <Card key={channelName} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">#{channelName}</CardTitle>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Activity className="h-4 w-4" />
                      {channelData.message_count} messages
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Last active: {formatDate(channelData.last_active)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {channelData.cache_status === "hit" && (
                      <div className="text-xs text-gray-400">
                        Summary generated:{" "}
                        {formatDate(channelData.generated_at)}
                      </div>
                    )}
                    <Markdown className="prose">{channelData.summary}</Markdown>
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      </ScrollArea>
    </div>
  );
}
