"use client";

import { useState } from "react";
import { Search } from "lucide-react";

interface TranscriptEntry {
  speaker: string;
  text: string;
  timestamp: string;
  language?: string;
}

interface TranscriptViewerProps {
  transcript: TranscriptEntry[];
  isLoading?: boolean;
}

export default function TranscriptViewer({
  transcript,
  isLoading = false,
}: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTranscript = transcript.filter(
    (entry) =>
      entry.speaker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-3 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search transcript..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3 rounded-lg bg-slate-800 bg-opacity-50 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400 focus:ring-opacity-20"
        />
      </div>

      {/* Transcript Entries */}
      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-slate-400">Loading transcript...</p>
            </div>
          </div>
        ) : filteredTranscript.length > 0 ? (
          filteredTranscript.map((entry, idx) => (
            <div
              key={idx}
              className="bg-slate-900 bg-opacity-50 p-4 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className="min-w-fit">
                  <span className="text-cyan-400 font-semibold text-sm block">
                    {entry.speaker}
                    {entry.language ? ` (${entry.language})` : ""}
                  </span>
                  <div className="text-xs text-slate-500 mt-1">
                    {entry.timestamp}
                  </div>
                </div>
                <p className="text-slate-200 text-sm leading-relaxed">
                  {entry.text}
                </p>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-400">
              {searchQuery ? "No matching entries found" : "No transcript available"}
            </p>
          </div>
        )}
      </div>

      {/* Result Count */}
      {searchQuery && (
        <p className="text-xs text-slate-500 text-center">
          {filteredTranscript.length} of {transcript.length} entries
        </p>
      )}
    </div>
  );
}