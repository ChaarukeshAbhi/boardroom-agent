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

  const [summary, setSummary] = useState("");
  const [askQuery, setAskQuery] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [comparison, setComparison] = useState("");

  const handleJoinMeeting = async () => {
    if (!meetingLink.trim()) {
      alert("Please enter a meeting link");
      return;
    }

    setLoading(true);
    setStatus("joining");
    setError("");

    try {
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

      if (!response.ok) {
        setStatus("error");
        setError(data.detail || "Failed to join meeting");
        return;
      }

      const bid = data.id || data.bot_id;

      setBotId(bid);
      setStatus("live");
    } catch (err) {
      console.error(err);
      setStatus("error");
      setError("Error joining meeting.");
    } finally {
      setLoading(false);
    }
  };

  const handleFetchTranscript = async () => {
    if (!botId) {
      alert("Bot ID not found.");
      return;
    }

    setFetchingTranscript(true);
    setError("");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/recall/transcript/${botId}`
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to fetch transcript");
        return;
      }

      if (data.transcript && Array.isArray(data.transcript)) {
        setTranscript(data.transcript);
        setStatus("completed");

        // store transcript
        await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/archive/store`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              bot_id: botId,
              transcript: data.transcript,
            }),
          }
        );
      }
    } catch (err) {
      console.error(err);
      setError("Error fetching transcript.");
    } finally {
      setFetchingTranscript(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!botId) return;

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/archive/summary/${botId}`
    );

    const data = await res.json();

    if (data.summary) setSummary(data.summary);
  };

  const handleAskAI = async () => {
    if (!askQuery.trim()) return;

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/archive/ask`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bot_id: botId,
          query: askQuery,
        }),
      }
    );

    const data = await res.json();

    if (data.answer) setAiAnswer(data.answer);
  };

  const handleCompareMeetings = async () => {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/archive/compare`
    );

    const data = await res.json();

    if (data.comparison) setComparison(data.comparison);
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

      {/* HEADER */}

      <header className="border-b border-slate-700 bg-slate-900 bg-opacity-50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-cyan-400 flex items-center justify-center">
              <Zap className="w-5 h-5 text-slate-900" />
            </div>
            <span className="text-cyan-400 font-bold text-xl">BoardRoom</span>
          </Link>

          <div className="flex gap-4">
            <Link href="/history" className="btn-transparent text-sm">
              History
            </Link>

            <Link href="/auth/login" className="btn-transparent text-sm">
              Logout
            </Link>
          </div>

        </div>
      </header>


      <main className="max-w-7xl mx-auto px-6 py-12">

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

          {/* LEFT */}

          <div className="space-y-8">

            <h1 className="text-5xl font-bold">
              From Conversations to
              <span className="block text-cyan-400">
                Actionable Intelligence
              </span>
            </h1>

            {/* MEETING INPUT */}

            <div className="card-dark space-y-4">

              <label className="text-sm font-semibold text-slate-200">
                Submit Meeting Link
              </label>

              <div className="flex gap-2">

                <input
                  type="url"
                  value={meetingLink}
                  onChange={(e) => setMeetingLink(e.target.value)}
                  placeholder="Paste meeting link"
                  className="flex-1 px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
                />

                <button
                  onClick={handleJoinMeeting}
                  disabled={loading}
                  className="btn-blue px-6 py-3 flex items-center gap-2"
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


            {/* STATUS */}

            <div className={`text-lg font-semibold ${getStatusColor()}`}>
              {getStatusText()}
            </div>


            {botId && status === "live" && (
              <button
                onClick={handleFetchTranscript}
                disabled={fetchingTranscript}
                className="btn-blue w-full py-4"
              >
                {fetchingTranscript ? "Fetching..." : "🎤 Fetch Transcript"}
              </button>
            )}


            {status === "completed" && (
              <button
                onClick={handleGenerateSummary}
                className="btn-blue w-full py-4"
              >
                Generate Summary
              </button>
            )}


            {/* ASK AI */}

            <div className="card-dark space-y-3">

              <h2 className="text-xl font-bold">Ask AI</h2>

              <input
                value={askQuery}
                onChange={(e) => setAskQuery(e.target.value)}
                placeholder="Ask about the meeting..."
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded"
              />

              <button
                onClick={handleAskAI}
                className="btn-blue px-6 py-2"
              >
                Ask
              </button>

              {aiAnswer && (
                <p className="text-sm text-slate-200">{aiAnswer}</p>
              )}

            </div>


            {/* COMPARE */}

            <button
              onClick={handleCompareMeetings}
              className="btn-blue px-6 py-3"
            >
              Compare Meetings
            </button>

            {comparison && (
              <div className="card-dark">
                <p className="text-sm text-slate-200">{comparison}</p>
              </div>
            )}

          </div>


          {/* RIGHT */}

          <div className="space-y-4">

            {summary && (
              <div className="card-dark-lg">
                <h2 className="text-xl font-bold text-cyan-400 mb-2">
                  AI Summary
                </h2>
                <p className="text-sm">{summary}</p>
              </div>
            )}

            {transcript.length > 0 ? (
              <div className="card-dark-lg space-y-3">

                <h2 className="text-2xl font-bold">Transcript</h2>

                <div className="max-h-[600px] overflow-y-auto space-y-3">

                  {transcript.map((line, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900 p-3 rounded border border-slate-700"
                    >
                      <p className="text-cyan-400 text-sm font-semibold">
                        {line.speaker}
                      </p>

                      <p className="text-xs text-slate-500">
                        {line.timestamp}
                      </p>

                      <p className="text-sm text-slate-200">
                        {line.text}
                      </p>
                    </div>
                  ))}

                </div>

              </div>
            ) : (
              <div className="card-dark-lg text-center py-12">
                No transcript yet
              </div>
            )}

          </div>

        </div>

      </main>

    </div>
  );
}