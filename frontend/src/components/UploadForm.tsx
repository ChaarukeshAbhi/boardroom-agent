"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";

export default function UploadForm() {
  const router = useRouter();
  const [meetingLink, setMeetingLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!meetingLink.trim()) {
      setError("Please enter a meeting link");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/meetings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meeting_link: meetingLink }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/meetings/${data.id}`);
      } else {
        setError("Failed to submit meeting. Please try again.");
      }
    } catch (err) {
      setError("Error submitting meeting. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full">
      <div className="flex gap-2">
        <input
          type="url"
          placeholder="Paste meeting link (Zoom, Google Meet, Teams...)"
          value={meetingLink}
          onChange={(e) => setMeetingLink(e.target.value)}
          className="flex-1 px-6 py-3 rounded-full bg-slate-800 bg-opacity-50 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400 focus:ring-opacity-20"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="btn-blue px-8 py-3 flex items-center gap-2"
        >
          <Upload className="w-4 h-4" />
          {loading ? "Processing..." : "Submit"}
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
    </form>
  );
}