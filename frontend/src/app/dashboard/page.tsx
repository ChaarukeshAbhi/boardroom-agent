"use client";

import { useState } from "react";
import { Zap, LinkIcon, Loader } from "lucide-react";
import Link from "next/link";

interface TranscriptLine {
  speaker: string;
  text: string;
  timestamp: string;
  confidence: number;
  language?: string;
}

export default function DashboardPage() {
  const [meetingLink, setMeetingLink] = useState("");
  const [agentName, setAgentName] = useState("BoardRoom Agent");
  const [loading, setLoading] = useState(false);
  const [fetchingTranscript, setFetchingTranscript] = useState(false);
  const [botId, setBotId] = useState<string | null>(null);
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [error, setError] = useState("");

  const handleJoinMeeting = async () => {
    if (!meetingLink.trim()) {
      alert("Please enter a meeting link");
      return;
    }

    setLoading(true);
    setStatus("joining");
    setError("");

    try {
      console.log("📍 Joining meeting:", meetingLink);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/recall/join`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            meeting_url: meetingLink,
            agent_name: agentName,
          }),
        }
      );

      const data = await response.json();
      console.log("✅ Response:", data);

      if (!response.ok) {
        console.error("❌ Error:", data);
        setStatus("error");
        setError(data.detail || "Failed to join meeting");
        return;
      }

      const bid = data.id || data.bot_id;
      console.log("🤖 Bot ID:", bid);

      setBotId(bid);
      setStatus("live");
    } catch (err) {
      console.error("❌ Error:", err);
      setStatus("error");
      setError("Error joining meeting. Check console.");
    } finally {
      setLoading(false);
    }
  };

  const handleFetchTranscript = async () => {
    if (!botId) {
      alert("Bot ID not found. Please join a meeting first.");
      return;
    }

    setFetchingTranscript(true);
    setError("");

    try {
      console.log("📥 Fetching transcript for bot:", botId);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/recall/transcript/${botId}`
      );

      const data = await response.json();
      console.log("✅ Transcript response:", data);

      if (!response.ok) {
        setError(data.detail || "Failed to fetch transcript");
        return;
      }

      if (data.transcript && Array.isArray(data.transcript)) {
        setTranscript(data.transcript);
        setStatus("completed");
      } else {
        setError("No transcript data received");
      }
    } catch (err) {
      console.error("❌ Error:", err);
      setError("Error fetching transcript. Check console.");
    } finally {
      setFetchingTranscript(false);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "joining":
        return "text-yellow-400";
      case "live":
        return "text-green-400";
      case "completed":
        return "text-purple-400";
      case "error":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "joining":
        return "⏳ Bot is joining...";
      case "live":
        return "🟢 Agent is live in meeting";
      case "completed":
        return "✅ Transcript ready!";
      case "error":
        return "❌ Error occurred";
      default:
        return "Ready to join";
    }
  };

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
          <Link href="/auth/login" className="btn-transparent text-sm">
            Logout
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Left Section */}
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold">
                From Conversations to
                <span className="block text-cyan-400">
                  Actionable Intelligence :)
                </span>
              </h1>
              <p className="text-slate-300 text-lg">
                BoardRoom Agent uses coordinated AI agents to transcribe, analyze, and remember meetings.
              </p>
            </div>

            {/* Meeting Link Input */}
            <div className="card-dark space-y-4">
              <label className="block text-sm font-semibold text-slate-200">
                Submit Meeting Link
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={meetingLink}
                  onChange={(e) => setMeetingLink(e.target.value)}
                  placeholder="Paste meeting link (Zoom, Google Meet, Teams...)"
                  className="flex-1 px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400 focus:ring-opacity-20"
                  disabled={loading}
                />
                <button
                  onClick={handleJoinMeeting}
                  disabled={loading || !meetingLink.trim()}
                  className="btn-blue px-6 py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <Loader className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <LinkIcon className="w-5 h-5" />
                      Join
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Status Display */}
            <div className={`flex items-center gap-2 text-lg font-semibold ${getStatusColor()}`}>
              {getStatusText()}
            </div>

            {/* Bot ID Display */}
            {botId && (
              <div className="bg-slate-800 bg-opacity-50 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-400 text-sm mb-2">Bot ID</p>
                <p className="text-cyan-400 font-mono break-all">{botId}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-500 bg-opacity-20 border border-red-500 text-red-300 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Fetch Transcript Button */}
            {botId && status === "live" && (
              <button
                onClick={handleFetchTranscript}
                disabled={fetchingTranscript}
                className="w-full btn-blue px-8 py-4 font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {fetchingTranscript ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Fetching Transcript...
                  </>
                ) : (
                  "🎤 Fetch Transcript"
                )}
              </button>
            )}

            {/* Quick Links */}
            <div className="space-y-3 pt-8 border-t border-slate-700">
              <Link href="/meetings" className="block card-dark p-4 hover:border-cyan-400 transition-all">
                <p className="font-semibold text-cyan-400">View All Meetings</p>
                <p className="text-sm text-slate-400 mt-1">Browse meeting history</p>
              </Link>
            </div>
          </div>

          {/* Right Section - Transcript Display */}
          <div className="relative">
            {transcript.length > 0 ? (
              <div className="card-dark-lg space-y-4">
                <h2 className="text-2xl font-bold">Transcript</h2>
                <div className="max-h-[600px] overflow-y-auto space-y-3 pr-4">
                  {transcript.map((line, idx) => (
                    <div key={idx} className="bg-slate-900 bg-opacity-50 p-3 rounded-lg border border-slate-700">
                      <div className="flex items-start gap-3">
                        <div className="min-w-fit">
                          <p className="text-cyan-400 font-semibold text-sm">
                            {line.speaker}
                            {line.language ? ` (${line.language})` : ""}
                          </p>
                          <p className="text-slate-500 text-xs">{line.timestamp}</p>
                        </div>
                        <p className="text-slate-200 text-sm">{line.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="card-dark-lg flex flex-col items-center justify-center py-12 text-center space-y-4">
                <p className="text-slate-400 text-lg">No transcript yet</p>
                <p className="text-slate-500 text-sm">
                  {botId && status === "live"
                    ? "Click 'Fetch Transcript' after the meeting ends."
                    : "Join a meeting to start recording."}
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="gradient-bottom h-20 mt-12"></footer>
    </div>
  );
}