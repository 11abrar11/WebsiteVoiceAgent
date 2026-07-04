/**
 * AdminDashboard Page
 * Protected dashboard for viewing conversations, transcripts, leads, and meetings.
 * Updated for lead-centric integer-PK schema.
 */
import { useState, useEffect, useCallback } from "react";
import { useLocation } from "wouter";
import logoFull from "@assets/logo-full.svg";

const API_BASE = "http://localhost:8001/api/admin";

interface ConversationSummary {
  id: number;
  email: string | null;
  started_at: string | null;
  ended_at: string | null;
  status: string;
  duration_seconds: number | null;
  message_count: number | null;
  escalated: boolean;
  lead: { name: string | null; company: string | null; email: string | null; phone: string | null; lead_score: number | null; lead_status: string | null } | null;
  summary: string | null;
}

interface Message {
  id: number;
  speaker: string;
  content: string;
  timestamp: string | null;
  message_type: string;
}

interface ConversationDetail {
  id: number;
  started_at: string | null;
  ended_at: string | null;
  status: string;
  duration_seconds: number | null;
  message_count: number | null;
  model_used: string | null;
  escalated: boolean;
  escalation_reason: string | null;
  lead: Record<string, unknown> | null;
  summary: { text: string; model: string | null; version: number; generated_at: string | null } | null;
  messages: Message[];
}

interface MeetingItem {
  id: number;
  date: string | null;
  time: string | null;
  status: string;
  notes: string | null;
  email: string | null;
  lead_name: string | null;
  created_at: string | null;
}

function getToken(): string | null {
  return localStorage.getItem("admin_token");
}

async function apiFetch(path: string) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    localStorage.removeItem("admin_token");
    window.location.href = "/voice-agent/admin";
    throw new Error("Unauthorized");
  }
  return res.json();
}

function formatDateTime(iso: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatTime(time24: string | null) {
  if (!time24) return "—";
  const [h, m] = time24.split(":");
  const hour = parseInt(h);
  const ampm = hour >= 12 ? "PM" : "AM";
  const h12 = hour % 12 || 12;
  return `${h12}:${m} ${ampm}`;
}

function formatDuration(seconds: number | null) {
  if (seconds == null) return "—";
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}

/* ─── Conversations Tab ─── */
function ConversationsView({
  onSelect,
}: {
  onSelect: (id: number) => void;
}) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/conversations?limit=50")
      .then((data) => {
        if (data && data.conversations) {
          setConversations(data.conversations);
        } else {
          setConversations([]);
        }
      })
      .catch((err) => {
        console.error(err);
        setConversations([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 p-8">Loading conversations...</div>;

  if (conversations.length === 0)
    return <div className="text-gray-500 p-8 text-center">No conversations yet.</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[#222] text-gray-400 text-sm">
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 font-medium">Email</th>
            <th className="pb-3 pr-4 font-medium">Name</th>
            <th className="pb-3 pr-4 font-medium">Status</th>
            <th className="pb-3 pr-4 font-medium">Duration</th>
            <th className="pb-3 pr-4 font-medium">Score</th>
            <th className="pb-3 font-medium">Summary</th>
          </tr>
        </thead>
        <tbody>
          {conversations.map((c) => (
            <tr
              key={c.id}
              onClick={() => onSelect(c.id)}
              className="border-b border-[#1a1a1a] hover:bg-[#111] cursor-pointer transition-colors"
            >
              <td className="py-4 pr-4 text-sm text-gray-300 whitespace-nowrap">
                {formatDateTime(c.started_at)}
              </td>
              <td className="py-4 pr-4 text-sm text-blue-400">
                {c.email || <span className="text-gray-500">—</span>}
              </td>
              <td className="py-4 pr-4 text-sm text-white">
                {c.lead?.name || <span className="text-gray-500">Unknown</span>}
              </td>
              <td className="py-4 pr-4">
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    c.status === "completed"
                      ? "bg-green-500/10 text-green-400"
                      : c.status === "active"
                      ? "bg-blue-500/10 text-blue-400"
                      : c.status === "failed"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-gray-500/10 text-gray-400"
                  }`}
                >
                  {c.status}
                </span>
              </td>
              <td className="py-4 pr-4 text-sm text-gray-300">
                {formatDuration(c.duration_seconds)}
              </td>
              <td className="py-4 pr-4 text-sm text-gray-300">
                {c.lead?.lead_score ?? "—"}
              </td>
              <td className="py-4 text-sm text-gray-400 max-w-xs truncate">
                {c.summary || "No summary"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Conversation Detail ─── */
function ConversationDetailView({
  conversationId,
  onBack,
}: {
  conversationId: number;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch(`/conversations/${conversationId}`)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [conversationId]);

  if (loading) return <div className="text-gray-400 p-8">Loading conversation...</div>;
  if (!detail) return <div className="text-red-400 p-8">Conversation not found.</div>;

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-[hsl(var(--primary))] hover:underline text-sm mb-4">
        ← Back to conversations
      </button>

      {/* Header */}
      <div className="bg-[#111] border border-[#222] rounded-xl p-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-white">
              {detail.lead?.name as string || "Unknown Visitor"}
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              {formatDateTime(detail.started_at)} → {formatDateTime(detail.ended_at)}
            </p>
            {detail.duration_seconds != null && (
              <p className="text-xs text-gray-500 mt-1">
                Duration: {formatDuration(detail.duration_seconds)} · {detail.message_count ?? 0} messages
                {detail.model_used && <span> · Model: {detail.model_used}</span>}
              </p>
            )}
          </div>
          <span
            className={`text-xs px-3 py-1 rounded-full font-medium ${
              detail.status === "completed"
                ? "bg-green-500/10 text-green-400"
                : detail.status === "failed"
                ? "bg-red-500/10 text-red-400"
                : "bg-blue-500/10 text-blue-400"
            }`}
          >
            {detail.status}
          </span>
        </div>
      </div>

      {/* Summary */}
      {detail.summary && (
        <div className="bg-[#111] border border-[#222] rounded-xl p-6">
          <h4 className="text-sm font-medium text-gray-400 mb-2">AI Summary</h4>
          <p className="text-gray-200 text-sm leading-relaxed">{detail.summary.text}</p>
          <p className="text-xs text-gray-600 mt-2">
            v{detail.summary.version}
            {detail.summary.model && <span> · {detail.summary.model}</span>}
            {detail.summary.generated_at && <span> · {formatDateTime(detail.summary.generated_at)}</span>}
          </p>
        </div>
      )}

      {/* Lead Info */}
      {detail.lead && (
        <div className="bg-[#111] border border-[#222] rounded-xl p-6">
          <h4 className="text-sm font-medium text-gray-400 mb-3">Lead Information</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            {Object.entries(detail.lead).map(([key, value]) => {
              if (key === "id" || key === "data_completeness") return null;
              return (
                <div key={key}>
                  <span className="text-gray-500 capitalize">{key.replace(/_/g, " ")}</span>
                  <p className="text-white mt-0.5">{(value as string) || "—"}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Transcript */}
      <div className="bg-[#111] border border-[#222] rounded-xl p-6">
        <h4 className="text-sm font-medium text-gray-400 mb-4">Transcript</h4>
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
          {detail.messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.speaker === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-xl px-4 py-3 text-sm ${
                  m.speaker === "user"
                    ? "bg-[hsl(var(--primary))]/10 text-green-300 border border-[hsl(var(--primary))]/20"
                    : "bg-[#1a1a1a] text-gray-200 border border-[#222]"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-gray-400 capitalize">
                    {m.speaker}
                  </span>
                  <span className="text-xs text-gray-600">
                    {m.timestamp ? new Date(m.timestamp).toLocaleTimeString("en-IN", { timeStyle: "short" }) : ""}
                  </span>
                </div>
                <p className="leading-relaxed">{m.content}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Meetings Tab ─── */
function MeetingsView() {
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/meetings?limit=50")
      .then((data) => {
        if (data && data.meetings) {
          setMeetings(data.meetings);
        } else {
          setMeetings([]);
        }
      })
      .catch((err) => {
        console.error(err);
        setMeetings([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 p-8">Loading meetings...</div>;

  if (meetings.length === 0)
    return <div className="text-gray-500 p-8 text-center">No meetings booked yet.</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[#222] text-gray-400 text-sm">
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 font-medium">Time</th>
            <th className="pb-3 pr-4 font-medium">Email</th>
            <th className="pb-3 pr-4 font-medium">Name</th>
            <th className="pb-3 pr-4 font-medium">Status</th>
            <th className="pb-3 pr-4 font-medium">Notes</th>
            <th className="pb-3 font-medium">Booked</th>
          </tr>
        </thead>
        <tbody>
          {meetings.map((m) => (
            <tr key={m.id} className="border-b border-[#1a1a1a]">
              <td className="py-4 pr-4 text-sm text-gray-300">{m.date || "—"}</td>
              <td className="py-4 pr-4 text-sm text-white">{formatTime(m.time)}</td>
              <td className="py-4 pr-4 text-sm text-blue-400">{m.email || "—"}</td>
              <td className="py-4 pr-4 text-sm text-gray-300">{m.lead_name || "—"}</td>
              <td className="py-4 pr-4">
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    m.status === "Reserved"
                      ? "bg-yellow-500/10 text-yellow-400"
                      : m.status === "Confirmed"
                      ? "bg-green-500/10 text-green-400"
                      : m.status === "Completed"
                      ? "bg-blue-500/10 text-blue-400"
                      : m.status === "No_Show"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-gray-500/10 text-gray-400"
                  }`}
                >
                  {m.status}
                </span>
              </td>
              <td className="py-4 pr-4 text-sm text-gray-400 max-w-xs truncate">
                {m.notes || "—"}
              </td>
              <td className="py-4 text-sm text-gray-500">{formatDateTime(m.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Main Dashboard ─── */
export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<"conversations" | "meetings">("conversations");
  const [selectedConversation, setSelectedConversation] = useState<number | null>(null);
  const [, navigate] = useLocation();

  // Auth guard
  useEffect(() => {
    if (!getToken()) {
      navigate("/voice-agent/admin");
    }
  }, [navigate]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("admin_token");
    navigate("/voice-agent/admin");
  }, [navigate]);

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Top Bar */}
      <header className="bg-[#0a0a0a] border-b border-[#222] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={logoFull} alt="PP5 Logo" className="h-8" />
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Logout
        </button>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Tab Navigation */}
        <div className="flex gap-1 mb-6 bg-[#111] rounded-xl p-1 w-fit">
          <button
            onClick={() => {
              setActiveTab("conversations");
              setSelectedConversation(null);
            }}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "conversations"
                ? "bg-[hsl(var(--primary))] text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Conversations
          </button>
          <button
            onClick={() => {
              setActiveTab("meetings");
              setSelectedConversation(null);
            }}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "meetings"
                ? "bg-[hsl(var(--primary))] text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Meetings
          </button>
        </div>

        {/* Content */}
        {activeTab === "conversations" && !selectedConversation && (
          <ConversationsView onSelect={setSelectedConversation} />
        )}
        {activeTab === "conversations" && selectedConversation && (
          <ConversationDetailView
            conversationId={selectedConversation}
            onBack={() => setSelectedConversation(null)}
          />
        )}
        {activeTab === "meetings" && <MeetingsView />}
      </div>
    </div>
  );
}
