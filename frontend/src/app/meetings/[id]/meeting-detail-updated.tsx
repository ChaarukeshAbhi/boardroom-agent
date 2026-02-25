"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { Zap, Download, Share2, Loader } from "lucide-react";
import Link from "next/link";
import TranscriptViewer from "@/components/TranscriptViewer";

interface BotStatus {
  bot_id: string;
  status: string;
  is_recording: boolean;
  has_audio: boolean;
  recording_count: number;
}

interface Transcript {
  speaker: string;
  text: string;
  timestamp: string;
  confidence: number;
}

export default function MeetingDetailPage() {
  const params = useParams();
  const [meeting, setMeeting] = useState<any>(null);
  const [transcript, setTranscript] = useState<Transcript[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState("idle");
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMeeting();
  }, [params.id]);

  const fetchMeeting = async () => {
    try {
      const response = await fetch(`/api/meetings/${params.id}`);
      if (response.ok) {
        const data = await response.json();
        const meetingData = data.meeting || data;
        setMeeting(meetingData);
        
        // Extract bot_id from different possible locations
        const bot_id = meetingData.bot_id || meetingData.id;
        if (bot_id) {
          console.log("Found bot_id:", bot_id);
        }
      }
    } catch (err) {
      console.error("Error fetching meeting:", err);
      setError("Failed to load meeting");
    } finally {
      setPageLoading(false);
    }
  };

  const checkAgentStatus = async () => {
    const bot_id = meeting?.bot_id || meeting?.id;
    
    if (!bot_id) {
      console.log("❌ No bot_id found");
      return;
    }

    try {
      console.log(`📊 Checking status for bot: ${bot_id}`);
      const response = await fetch(`/api/recall/status/${bot_id}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Status response:", data);
        
        setBotStatus(data);
        
        // Update agent status
        if (data.is_recording) {
          setAgentStatus("recording");
        } else if (data.has_audio) {
          setAgentStatus("ready");
        } else {
          setAgentStatus("idle");
        }
      } else {
        console.error("❌ Status check failed:", response.status);
        const error = await response.json();
        console.error("Error:", error);
      }
    } catch (error) {
      console.error("❌ Error checking bot status:", error);
    }
  };

  useEffect(() => {
    if (meeting) {
      console.log("Meeting loaded:", meeting);
      checkAgentStatus();
      
      // Poll every 2 seconds
      const interval = setInterval(checkAgentStatus, 2000);
      
      return () => clearInterval(interval);
    }
  }, [meeting]);

  const handleFetchTranscript = async () => {
    const bot_id = meeting?.bot_id || meeting?.id;
    
    if (!bot_id) {
      alert("No bot ID found");
      return;
    }

    setLoading(true);
    setError("");
    
    try {
      console.log(`📥 Fetching transcript for bot: ${bot_id}`);
      const response = await fetch(`/api/recall/transcript/${bot_id}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ Transcript response:", data);
        
        if (data.transcript && Array.isArray(data.transcript)) {
          setTranscript(data.transcript);
          setAgentStatus("completed");
        } else {
          setError("No transcript data received");
        }
      } else {
        const error = await response.json();
        console.error("❌ Error response:", error);
        setError(error.detail || "Failed to fetch transcript");
      }
    } catch (err) {
      console.error("❌ Error fetching transcript:", err);
      setError("Error fetching transcript. Check console.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch (agentStatus) {
      case "recording":
        return {
          color: "bg-blue-500 bg-opacity-20 text-blue-300",
          text: "🔴 Agent Recording",
        };
      case "ready":
        return {
          color: "bg-green-500 bg-opacity-20 text-green-300",
          text: "🟢 Ready for Transcript",
        };
      case "completed":
        return {
          color: "bg-purple-500 bg-opacity-20 text-purple-300",
          text: "✅ Transcript Ready",
        };
      default:
        return {
          color: "bg-yellow-500 bg-opacity-20 text-yellow-300",
          text: "⏳ Initializing...",
        };
    }
  };

  const statusBadge = getStatusBadge();

  if (pageLoading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-cyan-400 mx-auto mb-4" />
          <p className="text-slate-400">Loading meeting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900 bg-opacity-50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80">
            <div className="w-8 h-8 rounded-full bg-cyan-400 flex items-center justify-center">
              <Zap className="w-5 h-5 text-slate-900" />
            </div>
            <span className="text-cyan-400 font-bold text-xl">BoardRoom</span>
          </Link>
          <div className="flex gap-2">
            <button className="btn-transparent p-2 hover:border-cyan-300">
              <Download className="w-5 h-5" />
            </button>
            <button className="btn-transparent p-2 hover:border-cyan-300">
              <Share2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12 space-y-8">
        
        {/* Meeting Info */}
        <div className="space-y-4">
          <h1 className="text-4xl font-bold">Meeting Dashboard</h1>
          {meeting && (
            <div className="card-dark space-y-4">
              <div>
                <p className="text-slate-400 text-sm mb-1">Meeting Link</p>
                <p className="text-slate-200 break-all font-mono text-sm">{meeting.meeting_link || "N/A"}</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-1">Bot ID</p>
                <p className="text-cyan-400 font-mono text-sm">{meeting.bot_id || meeting.id || "Not assigned"}</p>
              </div>
            </div>
          )}
        </div>

        {/* Agent Status Section */}
        <div className="card-dark space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-4">Agent Status</h2>
            
            {/* Status Badge */}
            <div className={`px-4 py-3 rounded-lg ${statusBadge.color} inline-block mb-4`}>
              {statusBadge.text}
            </div>

            {/* Status Message */}
            <p className="text-slate-300 mt-4">
              {agentStatus === "recording" 
                ? "🎤 Agent is live in the meeting. Once the meeting ends, you can fetch the transcript."
                : agentStatus === "ready"
                ? "✅ Meeting ended. Audio is ready for transcription. Click below to generate transcript."
                : agentStatus === "completed"
                ? "🎉 Transcript is ready! Scroll down to view."
                : "⏳ Initializing agent status..."}
            </p>

            {/* Debug Info */}
            {botStatus && (
              <div className="mt-6 p-4 bg-slate-900 bg-opacity-50 rounded-lg text-xs text-slate-400 space-y-2">
                <p><span className="text-slate-500">Status:</span> {botStatus.status}</p>
                <p><span className="text-slate-500">Recording:</span> {botStatus.is_recording ? "Yes" : "No"}</p>
                <p><span className="text-slate-500">Has Audio:</span> {botStatus.has_audio ? "Yes" : "No"}</p>
                <p><span className="text-slate-500">Recordings:</span> {botStatus.recording_count}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Fetch Transcript Button */}
          <button
            onClick={handleFetchTranscript}
            disabled={loading || agentStatus === "recording" || agentStatus === "completed"}
            className={`w-full px-8 py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
              agentStatus === "ready" && !loading
                ? "btn-blue hover:bg-blue-600" 
                : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-50"
            }`}
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Processing Transcript...
              </>
            ) : agentStatus === "completed" ? (
              <>
                <span>✅ Transcript Generated</span>
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                Fetch Transcript
              </>
            )}
          </button>
        </div>

        {/* Transcript Section */}
        {transcript.length > 0 && (
          <div className="card-dark space-y-6">
            <h2 className="text-2xl font-bold">Full Transcript</h2>
            <TranscriptViewer transcript={transcript} isLoading={false} />
          </div>
        )}

        {/* Empty State */}
        {transcript.length === 0 && !loading && agentStatus !== "recording" && (
          <div className="card-dark text-center py-12 space-y-4">
            <p className="text-slate-400 text-lg">No transcript yet</p>
            <p className="text-slate-500 text-sm">
              {agentStatus === "ready" 
                ? "Click 'Fetch Transcript' to generate the transcript."
                : "Transcript will appear here once fetched."}
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="gradient-bottom h-20 mt-12"></footer>
    </div>
  );
}