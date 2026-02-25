"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import MeetingCard from "@/components/MeetingCard";


interface Meeting {
  id: string;
  title: string;
  meeting_link: string;
  date: string;
  duration: number;
  participants: string[];
  status: string;
  created_at: string;
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await fetch("/api/meetings");
      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings || []);
      }
    } catch (error) {
      console.error("Error fetching meetings:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-bg flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900 bg-opacity-50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80">
            <div className="w-8 h-8 rounded-full bg-cyan-400 flex items-center justify-center">
              <Zap className="w-5 h-5 text-slate-900" />
            </div>
            <span className="text-cyan-400 font-bold text-xl">BoardRoom</span>
          </Link>
          <Link href="/" className="btn-transparent">
            New Meeting
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-6 py-12">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12">
            <h1 className="text-4xl font-bold mb-2">All Meetings</h1>
            <p className="text-slate-400">View and manage your recorded meetings</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="w-12 h-12 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-400">Loading meetings...</p>
              </div>
            </div>
          ) : meetings.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-slate-400 text-lg">No meetings yet</p>
              <p className="text-slate-500 mt-2">Submit your first meeting link to get started</p>
              <Link href="/" className="btn-transparent mt-6 inline-block">
                Submit Meeting
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {meetings.map((meeting) => (
                <MeetingCard
                  key={meeting.id}
                  id={meeting.id}
                  title={meeting.title}
                  meeting_link={meeting.meeting_link}
                  date={meeting.date}
                  duration={meeting.duration}
                  participants={meeting.participants}
                  status={meeting.status}
                  created_at={meeting.created_at}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <footer className="gradient-bottom h-20"></footer>
    </div>
  );
}