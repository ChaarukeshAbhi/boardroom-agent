"use client";

import { Zap, ArrowRight, Check } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen gradient-bg">
      {/* Navigation */}
      <nav className="border-b border-slate-700 bg-slate-900 bg-opacity-50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-cyan-400 flex items-center justify-center">
              <Zap className="w-5 h-5 text-slate-900" />
            </div>
            <span className="text-cyan-400 font-bold text-xl">BoardRoom</span>
          </div>
          <div className="flex gap-3">
            <Link href="/auth/login" className="btn-transparent text-sm">
              Login
            </Link>
            <Link href="/auth/signup" className="btn-blue text-sm">
              Sign Up
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-8">
          <div className="space-y-4">
            <h1 className="text-6xl md:text-7xl font-bold leading-tight">
              Turn Meetings Into
              <span className="block bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Actionable Intelligence
              </span>
            </h1>
            <p className="text-xl text-slate-300 leading-relaxed">
              AI-powered meeting transcription, summarization, and insights. Never miss a decision or follow-up again.
            </p>
          </div>

          <div className="flex gap-4">
            <Link href="/meetings" className="btn-blue px-8 py-3 flex items-center gap-2">
              Get Started
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button className="btn-transparent px-8 py-3">
              Watch Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 pt-8 border-t border-slate-700">
            <div>
              <p className="text-3xl font-bold text-cyan-400">1000+</p>
              <p className="text-sm text-slate-400">Meetings Processed</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-cyan-400">99.9%</p>
              <p className="text-sm text-slate-400">Accuracy Rate</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-cyan-400">2min</p>
              <p className="text-sm text-slate-400">Processing Time</p>
            </div>
          </div>
        </div>

        {/* Hero Visual */}
        <div className="relative hidden lg:flex items-center justify-center">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-3xl opacity-20 blur-3xl"></div>
          <div className="card-dark-lg relative z-10 border-cyan-400 border-opacity-30">
            <div className="space-y-6">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-cyan-400 flex items-center justify-center text-sm font-bold">M</div>
                <div>
                  <p className="font-semibold text-white">Mary Chen</p>
                  <p className="text-xs text-slate-400">Project Manager</p>
                </div>
              </div>

              <div className="bg-slate-900 bg-opacity-50 p-4 rounded-xl border border-slate-700">
                <p className="text-sm text-cyan-400 font-semibold mb-2">MEETING SUMMARY</p>
                <ul className="space-y-2 text-slate-200 text-sm">
                  <li>✓ Q1 roadmap approved</li>
                  <li>✓ Budget allocation finalized</li>
                  <li>✓ Team assignments confirmed</li>
                  <li>✓ Next review: March 15</li>
                </ul>
              </div>

              <div className="flex gap-2">
                <button className="btn-transparent text-xs flex-1">View Transcript</button>
                <button className="btn-transparent text-xs flex-1">Export PDF</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold">Powerful Features</h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Everything you need to get the most out of your meetings
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: "Real-time Transcription",
              desc: "Accurate transcripts with speaker identification in 50+ languages",
              icon: "📝",
            },
            {
              title: "AI Summaries",
              desc: "Automatically generate brief summaries of key points and decisions",
              icon: "✨",
            },
            {
              title: "Action Items",
              desc: "Extract and track follow-ups and action items automatically",
              icon: "✅",
            },
            {
              title: "Search & Analytics",
              desc: "Find insights across all your meetings with powerful search",
              icon: "🔍",
            },
            {
              title: "Smart Insights",
              desc: "Identify patterns, trends, and important discussions",
              icon: "💡",
            },
            {
              title: "Easy Integration",
              desc: "Works with Zoom, Google Meet, Teams, and more",
              icon: "🔗",
            },
          ].map((feature, idx) => (
            <div key={idx} className="card-dark group hover:border-cyan-400 hover:border-opacity-50 transition-all">
              <p className="text-4xl mb-4">{feature.icon}</p>
              <h3 className="text-lg font-bold mb-2 group-hover:text-cyan-400 transition-colors">
                {feature.title}
              </h3>
              <p className="text-slate-400 text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold">Simple Pricing</h2>
          <p className="text-slate-400 text-lg">Choose the plan that works for you</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              name: "Starter",
              price: "Free",
              desc: "Perfect for individuals",
              features: ["5 meetings/month", "Basic transcription", "Simple summaries"],
            },
            {
              name: "Professional",
              price: "$29",
              period: "/month",
              desc: "For teams and professionals",
              features: ["Unlimited meetings", "Real-time transcription", "Advanced summaries", "Action item tracking"],
              highlighted: true,
            },
            {
              name: "Enterprise",
              price: "Custom",
              desc: "For large organizations",
              features: ["Everything in Pro", "Custom integrations", "Priority support", "Advanced analytics"],
            },
          ].map((plan, idx) => (
            <div
              key={idx}
              className={`card-dark p-8 relative ${
                plan.highlighted ? "border-cyan-400 border-opacity-100 md:scale-105" : ""
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-cyan-400 text-slate-900 px-4 py-1 rounded-full text-xs font-bold">
                  POPULAR
                </div>
              )}
              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <p className="text-slate-400 text-sm mb-4">{plan.desc}</p>
              <div className="mb-6">
                <span className="text-4xl font-bold">{plan.price}</span>
                {plan.period && <span className="text-slate-400">{plan.period}</span>}
              </div>
              <button
                className={`w-full mb-6 py-3 rounded-full font-semibold transition-all ${
                  plan.highlighted
                    ? "bg-cyan-400 text-slate-900 hover:bg-cyan-300"
                    : "btn-transparent"
                }`}
              >
                Get Started
              </button>
              <div className="space-y-3">
                {plan.features.map((feature, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-cyan-400" />
                    <span className="text-slate-300">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center space-y-6">
        <h2 className="text-4xl font-bold">Ready to Transform Your Meetings?</h2>
        <p className="text-xl text-slate-300">Join thousands of professionals using BoardRoom to stay on top of their meetings.</p>
        <Link href="/auth/signup" className="btn-blue px-8 py-3 inline-flex items-center gap-2">
          Start Free Trial
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="gradient-bottom h-20 mt-12"></footer>
    </div>
  );
}