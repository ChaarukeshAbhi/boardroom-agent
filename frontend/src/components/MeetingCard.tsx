"use client";

import Link from "next/link";
import { Calendar, Users, Clock, ArrowRight } from "lucide-react";

interface MeetingCardProps {
  id: string;
  title: string;
  meeting_link: string;
  date: string;
  duration: number;
  participants: string[];
  status: string;
  created_at: string;
}

export default function MeetingCard({
  id,
  title,
  meeting_link,
  date,
  duration,
  participants,
  status,
  created_at,
}: MeetingCardProps) {
  const getStatusBadgeColor = () => {
    switch (status) {
      case "completed":
        return "bg-green-500 bg-opacity-20 text-green-300";
      case "processing":
        return "bg-blue-500 bg-opacity-20 text-blue-300";
      case "failed":
        return "bg-red-500 bg-opacity-20 text-red-300";
      default:
        return "bg-yellow-500 bg-opacity-20 text-yellow-300";
    }
  };

  return (
    <Link href={`/meetings/${id}`} className="group">
      <div className="card-dark group-hover:border-cyan-400 group-hover:border-opacity-50 transition-all duration-300 cursor-pointer h-full flex flex-col justify-between">
        {/* Header */}
        <div>
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white group-hover:text-cyan-400 transition-colors truncate">
                {title || "Untitled Meeting"}
              </h3>
              <p className="text-sm text-slate-400 mt-1 truncate">
                {meeting_link}
              </p>
            </div>
            <span
              className={`ml-2 px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${getStatusBadgeColor()}`}
            >
              {status}
            </span>
          </div>

          {/* Metadata */}
          <div className="space-y-3 mt-6">
            <div className="flex items-center gap-2 text-slate-300">
              <Calendar className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span className="text-sm">
                {new Date(date).toLocaleDateString()}
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Clock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span className="text-sm">{duration} min</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Users className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span className="text-sm">{participants.length} participants</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-700 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {new Date(created_at).toLocaleDateString()}
          </span>
          <ArrowRight className="w-4 h-4 text-cyan-400 group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </Link>
  );
}