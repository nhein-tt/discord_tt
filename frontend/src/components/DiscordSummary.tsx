import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, RefreshCw, Trash2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Markdown from "react-markdown";

// Configuration constants
const ADMIN_PASSWORD = "nhein-tt";
const SERVER_ID = "863154240319258674";
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Tenstorrent brand colors
const THEME = {
  purple: {
    accent: "#7C68FA", // Tens Purple
    light: "#BCB3F7", // Purple Primary
    lighter: "#E2DEFC", // Purple++
  },
  blue: {
    accent: "#5164E0", // Blue Accent
    light: "#7584E6", // Blue Primary
    lighter: "#CCD2F9", // Blue++
  },
  slate: {
    accent: "#606891", // Slate Accent
    light: "#737999", // Slate Primary
    lighter: "#EDEFF9", // Slate++
    dark: "#101636", // Slate-
  },
  red: {
    accent: "#FA512E", // Red Accent
    light: "#FF9E8A", // Red Primary
  },
};

// Type definitions
interface ChannelSummary {
  summary: string;
  message_count: number;
  last_active: string;
  cache_status?: string;
  generated_at?: string;
}

interface SummaryResponse {
  server_id: string;
  timestamp: string;
  channels: Record<string, ChannelSummary>;
}

interface PasswordDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  loading: boolean;
}

// Password dialog component for admin actions
const PasswordDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  loading,
}: PasswordDialogProps) => {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      onConfirm();
      setPassword("");
      setError("");
    } else {
      setError("Incorrect password");
    }
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={() => {
        onClose();
        setPassword("");
        setError("");
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-slate-800">{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="col-span-3"
              />
              {error && <p className="text-red-500 text-sm">{error}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button
              type="submit"
              disabled={loading}
              style={{ backgroundColor: THEME.purple.accent }}
              className="hover:bg-opacity-90"
            >
              {loading ? "Processing..." : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Main Discord Summary Component
export function DiscordSummary() {
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
    });
  };

  const getDateRangeString = (currentDate: string) => {
    const endDate = new Date(currentDate);
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 7);

    return `${formatDate(startDate.toISOString())} - ${formatDate(endDate.toISOString())}`;
  };

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/summarize/${SERVER_ID}`);
      if (!response.ok) throw new Error("Failed to fetch summary");
      const data = await response.json();
      setSummaryData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      const endpoint = `${API_BASE}/sync/${SERVER_ID}`;
      console.log(endpoint);
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error("Sync failed");
      setSyncDialogOpen(false);
      await fetchSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleClearCache = async () => {
    try {
      setClearing(true);
      const response = await fetch(`${API_BASE}/clear-cache/${SERVER_ID}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Cache clear failed");
      setClearDialogOpen(false);
      await fetchSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cache clear failed");
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => {
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

  return (
    <div
      className="space-y-6 bg-slate-50 p-6 rounded-lg"
      style={{ backgroundColor: THEME.slate.lighter }}
    >
      {/* Header Section */}
      <div className="space-y-2">
        <h1
          className="text-3xl font-bold flex items-center gap-2"
          style={{ color: THEME.slate.dark }}
        >
          Activity Dashboard
        </h1>
        <p className="text-lg" style={{ color: THEME.slate.accent }}>
          Channel discussions and updates
        </p>
      </div>

      {/* Timeline and Actions Bar */}
      <div
        className="flex items-center justify-between p-4 rounded-lg shadow-sm"
        style={{ backgroundColor: THEME.purple.lighter }}
      >
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5" style={{ color: THEME.purple.accent }} />
          <span className="text-sm" style={{ color: THEME.slate.accent }}>
            Summary Timeline:{" "}
            {summaryData && getDateRangeString(summaryData.timestamp)}
          </span>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setSyncDialogOpen(true)}
            disabled={syncing}
            variant="outline"
            className="flex items-center gap-2 hover:bg-opacity-90"
            style={{
              borderColor: THEME.purple.accent,
              color: THEME.purple.accent,
            }}
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Syncing..." : "Force Sync"}
          </Button>
          <Button
            onClick={() => setClearDialogOpen(true)}
            disabled={clearing}
            variant="outline"
            className="flex items-center gap-2 hover:bg-opacity-90"
            style={{
              borderColor: THEME.red.accent,
              color: THEME.red.accent,
            }}
          >
            <Trash2 className="h-4 w-4" />
            {clearing ? "Clearing..." : "Clear Cache"}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div
          className="p-4 rounded-md"
          style={{
            backgroundColor: THEME.red.light,
            color: THEME.red.accent,
          }}
        >
          Error: {error}
        </div>
      )}

      {/* Password Dialogs */}
      <PasswordDialog
        isOpen={syncDialogOpen}
        onClose={() => setSyncDialogOpen(false)}
        onConfirm={handleSync}
        title="Confirm Force Sync"
        description="Please enter the admin password to force sync all channels."
        loading={syncing}
      />

      <PasswordDialog
        isOpen={clearDialogOpen}
        onClose={() => setClearDialogOpen(false)}
        onConfirm={handleClearCache}
        title="Confirm Cache Clear"
        description="Please enter the admin password to clear the summary cache."
        loading={clearing}
      />

      {/* No Data State */}
      {!summaryData || Object.keys(summaryData.channels).length === 0 ? (
        <div style={{ color: THEME.slate.accent }} className="p-4">
          No active channels found in the past week
        </div>
      ) : (
        <>
          {/* Last Update Timestamp */}
          <div className="text-sm" style={{ color: THEME.slate.accent }}>
            Last updated: {formatDate(summaryData.timestamp)}
          </div>

          {/* Channel Summaries */}
          <ScrollArea className="h-[800px] pr-4">
            <div className="space-y-4">
              {Object.entries(summaryData.channels)
                .sort(
                  ([, a], [, b]) =>
                    new Date(b.last_active).getTime() -
                    new Date(a.last_active).getTime(),
                )
                .map(([channelName, channelData]) => (
                  <Card
                    key={channelName}
                    className="border-l-4"
                    style={{
                      borderLeftColor: THEME.purple.accent,
                      backgroundColor: THEME.purple.lighter,
                    }}
                  >
                    <CardHeader
                      className="bg-opacity-50"
                      style={{ backgroundColor: THEME.purple.lighter }}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle
                          className="text-xl font-medium"
                          style={{ color: THEME.slate.dark }}
                        >
                          #{channelName}
                        </CardTitle>
                        <div
                          className="flex items-center gap-2 text-sm"
                          style={{ color: THEME.slate.accent }}
                        >
                          <Activity className="h-4 w-4" />
                          {channelData.message_count} messages
                        </div>
                      </div>
                      <div
                        className="text-sm"
                        style={{ color: THEME.slate.accent }}
                      >
                        Last active: {formatDate(channelData.last_active)}
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <div className="space-y-4">
                        {channelData.cache_status === "hit" && (
                          <div
                            className="text-xs"
                            style={{ color: THEME.slate.accent }}
                          >
                            Generated: {formatDate(channelData.generated_at)}
                          </div>
                        )}
                        <Markdown
                          className="prose max-w-none"
                          components={{
                            p: ({ children }) => (
                              <p style={{ color: THEME.slate.dark }}>
                                {children}
                              </p>
                            ),
                          }}
                        >
                          {channelData.summary}
                        </Markdown>
                      </div>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </ScrollArea>
        </>
      )}
    </div>
  );
}

// import React, { useState, useEffect } from "react";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Skeleton } from "@/components/ui/skeleton";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { Activity, RefreshCw, Trash2, Clock } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import {
//   Dialog,
//   DialogContent,
//   DialogDescription,
//   DialogFooter,
//   DialogHeader,
//   DialogTitle,
// } from "@/components/ui/dialog";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import Markdown from "react-markdown";

// // Configuration constants
// const ADMIN_PASSWORD = "nhein-tt"; // In production, this should be an environment variable
// const SERVER_ID = "863154240319258674";
// const API_BASE = "http://localhost:8000";

// // Tenstorrent brand colors and theme configuration
// const THEME = {
//   primary: "#0066CC", // Tenstorrent blue
//   secondary: "#00A3E0", // Secondary blue for accents
//   background: "#F5F7FA", // Light background
//   text: "#1A1A1A", // Dark text for contrast
// };

// // Type definitions for our data structure
// interface ChannelSummary {
//   summary: string;
//   message_count: number;
//   last_active: string;
//   cache_status?: string;
//   generated_at?: string;
// }

// interface SummaryResponse {
//   server_id: string;
//   timestamp: string;
//   channels: Record<string, ChannelSummary>;
// }

// // Props interface for the password dialog component
// interface PasswordDialogProps {
//   isOpen: boolean;
//   onClose: () => void;
//   onConfirm: () => void;
//   title: string;
//   description: string;
//   loading: boolean;
// }

// // Reusable password dialog component for admin actions
// const PasswordDialog = ({
//   isOpen,
//   onClose,
//   onConfirm,
//   title,
//   description,
//   loading,
// }: PasswordDialogProps) => {
//   const [password, setPassword] = useState("");
//   const [error, setError] = useState("");

//   const handleSubmit = (e: React.FormEvent) => {
//     e.preventDefault();
//     if (password === ADMIN_PASSWORD) {
//       onConfirm();
//       setPassword("");
//       setError("");
//     } else {
//       setError("Incorrect password");
//     }
//   };

//   return (
//     <Dialog
//       open={isOpen}
//       onOpenChange={() => {
//         onClose();
//         setPassword("");
//         setError("");
//       }}
//     >
//       <DialogContent className="sm:max-w-md">
//         <DialogHeader>
//           <DialogTitle>{title}</DialogTitle>
//           <DialogDescription>{description}</DialogDescription>
//         </DialogHeader>
//         <form onSubmit={handleSubmit}>
//           <div className="grid gap-4 py-4">
//             <div className="grid gap-2">
//               <Label htmlFor="password">Password</Label>
//               <Input
//                 id="password"
//                 type="password"
//                 value={password}
//                 onChange={(e) => setPassword(e.target.value)}
//                 disabled={loading}
//                 className="col-span-3"
//               />
//               {error && <p className="text-sm text-red-500">{error}</p>}
//             </div>
//           </div>
//           <DialogFooter>
//             <Button type="submit" disabled={loading}>
//               {loading ? "Processing..." : "Confirm"}
//             </Button>
//           </DialogFooter>
//         </form>
//       </DialogContent>
//     </Dialog>
//   );
// };

// // Main Discord Summary Component
// export function DiscordSummary() {
//   // State management for data and UI
//   const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [syncing, setSyncing] = useState(false);
//   const [clearing, setClearing] = useState(false);
//   const [syncDialogOpen, setSyncDialogOpen] = useState(false);
//   const [clearDialogOpen, setClearDialogOpen] = useState(false);

//   // Utility function to format dates consistently
//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleString("en-US", {
//       weekday: "short",
//       month: "short",
//       day: "numeric",
//       hour: "numeric",
//       minute: "numeric",
//     });
//   };

//   // API call to fetch summary data
//   const fetchSummary = async () => {
//     try {
//       setLoading(true);
//       const response = await fetch(`${API_BASE}/summarize/${SERVER_ID}`);
//       if (!response.ok) throw new Error("Failed to fetch summary");
//       const data = await response.json();
//       setSummaryData(data);
//     } catch (err) {
//       setError(err instanceof Error ? err.message : "An error occurred");
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Handler for force sync action
//   const handleSync = async () => {
//     try {
//       setSyncing(true);
//       const response = await fetch(`${API_BASE}/sync/${SERVER_ID}`);
//       if (!response.ok) throw new Error("Sync failed");
//       setSyncDialogOpen(false);
//       await fetchSummary();
//     } catch (err) {
//       setError(err instanceof Error ? err.message : "Sync failed");
//     } finally {
//       setSyncing(false);
//     }
//   };

//   // Handler for clearing cache
//   const handleClearCache = async () => {
//     try {
//       setClearing(true);
//       const response = await fetch(`${API_BASE}/clear-cache/${SERVER_ID}`, {
//         method: "POST",
//       });
//       if (!response.ok) throw new Error("Cache clear failed");
//       setClearDialogOpen(false);
//       await fetchSummary();
//     } catch (err) {
//       setError(err instanceof Error ? err.message : "Cache clear failed");
//     } finally {
//       setClearing(false);
//     }
//   };

//   // Initial data fetch on component mount
//   useEffect(() => {
//     fetchSummary();
//   }, []);

//   // Loading state UI
//   if (loading) {
//     return (
//       <div className="space-y-4">
//         {[1, 2, 3].map((i) => (
//           <Skeleton key={i} className="h-64 w-full" />
//         ))}
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-6 bg-slate-50 p-6 rounded-lg">
//       {/* Header Section */}
//       <div className="space-y-2">
//         <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
//           Activity Dashboard
//         </h1>
//         <p className="text-slate-600 text-lg">
//           Channel discussions and updates
//         </p>
//       </div>

//       {/* Timeline and Actions Bar */}
//       <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
//         <div className="flex items-center gap-2">
//           <Clock className="h-5 w-5 text-blue-600" />
//           <span className="text-sm text-slate-600">
//             Summary Timeline: Last 7 days
//           </span>
//         </div>
//         <div className="flex gap-2">
//           <Button
//             onClick={() => setSyncDialogOpen(true)}
//             disabled={syncing}
//             variant="outline"
//             className="flex items-center gap-2 hover:bg-blue-50"
//           >
//             <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
//             {syncing ? "Syncing..." : "Force Sync"}
//           </Button>
//           <Button
//             onClick={() => setClearDialogOpen(true)}
//             disabled={clearing}
//             variant="outline"
//             className="flex items-center gap-2 hover:bg-blue-50"
//           >
//             <Trash2 className="h-4 w-4" />
//             {clearing ? "Clearing..." : "Clear Cache"}
//           </Button>
//         </div>
//       </div>

//       {/* Error Display */}
//       {error && (
//         <div className="text-red-500 p-4 rounded-md bg-red-50">
//           Error: {error}
//         </div>
//       )}

//       {/* Password Dialogs */}
//       <PasswordDialog
//         isOpen={syncDialogOpen}
//         onClose={() => setSyncDialogOpen(false)}
//         onConfirm={handleSync}
//         title="Confirm Force Sync"
//         description="Please enter the admin password to force sync all channels."
//         loading={syncing}
//       />

//       <PasswordDialog
//         isOpen={clearDialogOpen}
//         onClose={() => setClearDialogOpen(false)}
//         onConfirm={handleClearCache}
//         title="Confirm Cache Clear"
//         description="Please enter the admin password to clear the summary cache."
//         loading={clearing}
//       />

//       {/* No Data State */}
//       {!summaryData || Object.keys(summaryData.channels).length === 0 ? (
//         <div className="text-gray-500 p-4">
//           No active channels found in the past week
//         </div>
//       ) : (
//         <>
//           {/* Last Update Timestamp */}
//           <div className="text-sm text-gray-500">
//             Last updated: {formatDate(summaryData.timestamp)}
//           </div>

//           {/* Channel Summaries */}
//           <ScrollArea className="h-[800px] pr-4">
//             <div className="space-y-4">
//               {Object.entries(summaryData.channels)
//                 .sort(
//                   ([, a], [, b]) =>
//                     new Date(b.last_active).getTime() -
//                     new Date(a.last_active).getTime(),
//                 )
//                 .map(([channelName, channelData]) => (
//                   <Card
//                     key={channelName}
//                     className="border-l-4"
//                     style={{ borderLeftColor: THEME.primary }}
//                   >
//                     <CardHeader className="bg-slate-50">
//                       <div className="flex items-center justify-between">
//                         <CardTitle className="text-xl font-medium">
//                           #{channelName}
//                         </CardTitle>
//                         <div className="flex items-center gap-2 text-sm text-slate-600">
//                           <Activity className="h-4 w-4" />
//                           {channelData.message_count} messages
//                         </div>
//                       </div>
//                       <div className="text-sm text-slate-500">
//                         Last active: {formatDate(channelData.last_active)}
//                       </div>
//                     </CardHeader>
//                     <CardContent className="pt-4">
//                       <div className="space-y-4">
//                         {channelData.cache_status === "hit" && (
//                           <div className="text-xs text-slate-400">
//                             Generated: {formatDate(channelData.generated_at)}
//                           </div>
//                         )}
//                         <Markdown className="prose max-w-none">
//                           {channelData.summary}
//                         </Markdown>
//                       </div>
//                     </CardContent>
//                   </Card>
//                 ))}
//             </div>
//           </ScrollArea>
//         </>
//       )}
//     </div>
//   );
// }
