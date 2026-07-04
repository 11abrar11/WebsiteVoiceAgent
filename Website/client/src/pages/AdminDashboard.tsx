/**
 * AdminDashboard Page
 * Lead-centric CRM dashboard for viewing leads, metrics, conversations, and meetings.
 */
import { useState, useEffect, useCallback } from "react";
import { useLocation } from "wouter";
import logoFull from "@assets/logo-full.svg";

const API_BASE = "http://localhost:8001/api/admin";

interface DashboardMetricsData {
  total_leads: number;
  qualified_leads: number;
  meetings_booked: number;
  upcoming_meetings: number;
  average_lead_score: number;
  average_data_completeness: number;
}

interface LeadSummary {
  id: number;
  name: string | null;
  email: string | null;
  company: string | null;
  industry: string | null;
  lead_score: number | null;
  lead_status: string | null;
  data_completeness: number | null;
  conversation_count: number;
  meeting_count: number;
  last_interaction: string | null;
  created_at: string | null;
}

interface Conversation {
  id: number;
  started_at: string | null;
  ended_at: string | null;
  status: string;
  duration_seconds: number | null;
  model_used: string | null;
  summary: string | null;
  messages: { speaker: string; content: string; timestamp: string | null }[];
}

interface Meeting {
  id: number;
  date: string | null;
  time: string | null;
  status: string;
  notes: string | null;
}

interface LeadDetail {
  id: number;
  email: string | null;
  name: string | null;
  phone: string | null;
  company: string | null;
  industry: string | null;
  requirement: string | null;
  monthly_leads: string | null;
  company_size: string | null;
  budget: string | null;
  timeline: string | null;
  decision_maker: string | null;
  lead_score: number | null;
  lead_status: string | null;
  data_completeness: number | null;
  created_at: string | null;
  updated_at: string | null;
  business_summary: string | null;
  conversations: Conversation[];
  meetings: Meeting[];
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

/* ─── Dashboard Metrics ─── */
function DashboardMetrics() {
  const [metrics, setMetrics] = useState<DashboardMetricsData | null>(null);

  useEffect(() => {
    apiFetch("/metrics").then(setMetrics).catch(console.error);
  }, []);

  if (!metrics) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Total Leads</p>
        <p className="text-2xl font-bold text-white">{metrics.total_leads}</p>
      </div>
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Qualified Leads</p>
        <p className="text-2xl font-bold text-green-400">{metrics.qualified_leads}</p>
      </div>
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Meetings Booked</p>
        <p className="text-2xl font-bold text-blue-400">{metrics.meetings_booked}</p>
      </div>
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Upcoming Mtgs</p>
        <p className="text-2xl font-bold text-purple-400">{metrics.upcoming_meetings}</p>
      </div>
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Avg Lead Score</p>
        <p className="text-2xl font-bold text-yellow-400">{metrics.average_lead_score}</p>
      </div>
      <div className="bg-[#111] border border-[#222] p-4 rounded-xl">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Avg Data Quality</p>
        <p className="text-2xl font-bold text-indigo-400">{metrics.average_data_completeness}%</p>
      </div>
    </div>
  );
}

/* ─── Leads Tab ─── */
function LeadsView({ onSelect }: { onSelect: (id: number) => void }) {
  const [leads, setLeads] = useState<LeadSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const fetchLeads = useCallback(() => {
    setLoading(true);
    let url = "/leads?limit=50";
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

    apiFetch(url)
      .then((data) => {
        if (data && data.leads) setLeads(data.leads);
        else setLeads([]);
      })
      .catch((err) => {
        console.error(err);
        setLeads([]);
      })
      .finally(() => setLoading(false));
  }, [search, statusFilter]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Search by name, email, company..."
          className="bg-[#111] border border-[#222] text-white px-4 py-2 rounded-lg text-sm w-80 focus:outline-none focus:border-[hsl(var(--primary))]"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchLeads()}
        />
        <select
          className="bg-[#111] border border-[#222] text-white px-4 py-2 rounded-lg text-sm focus:outline-none focus:border-[hsl(var(--primary))]"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="Cold">Cold</option>
          <option value="Warm">Warm</option>
          <option value="Hot">Hot</option>
        </select>
        <button
          onClick={fetchLeads}
          className="bg-[#1a1a1a] hover:bg-[#222] border border-[#333] px-4 py-2 rounded-lg text-sm transition-colors"
        >
          Apply Filters
        </button>
      </div>

      {loading ? (
        <div className="text-gray-400 p-8">Loading leads...</div>
      ) : leads.length === 0 ? (
        <div className="text-gray-500 p-8 text-center bg-[#111] border border-[#222] rounded-xl">No leads found.</div>
      ) : (
        <div className="overflow-x-auto bg-[#111] border border-[#222] rounded-xl">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#222] text-gray-400 text-sm">
                <th className="py-4 pl-6 pr-4 font-medium">Name</th>
                <th className="py-4 pr-4 font-medium">Company</th>
                <th className="py-4 pr-4 font-medium">Score</th>
                <th className="py-4 pr-4 font-medium">Status</th>
                <th className="py-4 pr-4 font-medium">Conversations</th>
                <th className="py-4 pr-4 font-medium">Meetings</th>
                <th className="py-4 pr-6 font-medium">Last Interaction</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => onSelect(lead.id)}
                  className="border-b border-[#1a1a1a] hover:bg-[#1a1a1a] cursor-pointer transition-colors"
                >
                  <td className="py-4 pl-6 pr-4">
                    <p className="text-sm font-medium text-white">{lead.name || "Unknown"}</p>
                    <p className="text-xs text-blue-400 mt-1">{lead.email}</p>
                  </td>
                  <td className="py-4 pr-4 text-sm text-gray-300">
                    {lead.company || <span className="text-gray-500">—</span>}
                    {lead.industry && <p className="text-xs text-gray-500 mt-1">{lead.industry}</p>}
                  </td>
                  <td className="py-4 pr-4 text-sm text-white font-medium">{lead.lead_score ?? "—"}</td>
                  <td className="py-4 pr-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${
                        lead.lead_status === "Hot"
                          ? "bg-red-500/10 text-red-400"
                          : lead.lead_status === "Warm"
                          ? "bg-yellow-500/10 text-yellow-400"
                          : "bg-blue-500/10 text-blue-400"
                      }`}
                    >
                      {lead.lead_status || "Cold"}
                    </span>
                  </td>
                  <td className="py-4 pr-4 text-sm text-gray-300">{lead.conversation_count}</td>
                  <td className="py-4 pr-4 text-sm text-gray-300">{lead.meeting_count}</td>
                  <td className="py-4 pr-6 text-sm text-gray-400 whitespace-nowrap">
                    {formatDateTime(lead.last_interaction)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ─── Lead Detail View ─── */
function LeadDetailView({ leadId, onBack }: { leadId: number; onBack: () => void }) {
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedConv, setExpandedConv] = useState<number | null>(null);

  useEffect(() => {
    apiFetch(`/leads/${leadId}`)
      .then(setLead)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [leadId]);

  if (loading) return <div className="text-gray-400 p-8">Loading CRM profile...</div>;
  if (!lead) return <div className="text-red-400 p-8">Lead not found.</div>;

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-[hsl(var(--primary))] hover:underline text-sm mb-2 flex items-center gap-2">
        <span>←</span> Back to Leads
      </button>

      {/* Section A: Lead Profile */}
      <div className="bg-[#111] border border-[hsl(var(--primary))]/20 rounded-xl p-6 shadow-lg shadow-[hsl(var(--primary))]/5">
        <div className="flex justify-between items-start mb-6 border-b border-[#222] pb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">{lead.name || "Unknown Lead"}</h2>
            <p className="text-blue-400">{lead.email}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-white mb-1">{lead.lead_score ?? 0}</p>
            <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Lead Score</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Status</span>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
              lead.lead_status === 'Hot' ? 'bg-red-500/20 text-red-400' : 
              lead.lead_status === 'Warm' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'
            }`}>{lead.lead_status || "Cold"}</span>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Company</span>
            <p className="text-gray-200">{lead.company || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Industry</span>
            <p className="text-gray-200">{lead.industry || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Phone</span>
            <p className="text-gray-200">{lead.phone || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Budget</span>
            <p className="text-gray-200">{lead.budget || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Timeline</span>
            <p className="text-gray-200">{lead.timeline || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Decision Maker</span>
            <p className="text-gray-200 capitalize">{lead.decision_maker || "—"}</p>
          </div>
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Data Completeness</span>
            <p className="text-gray-200">{(lead.data_completeness ?? 0) * 100}%</p>
          </div>
          <div className="col-span-2 md:col-span-4">
            <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold block mb-1">Requirement</span>
            <p className="text-gray-200 bg-[#1a1a1a] p-3 rounded-lg border border-[#222]">{lead.requirement || "No specific requirements captured yet."}</p>
          </div>
        </div>
      </div>

      {/* Section B: AI Business Summary */}
      <div className="bg-[#111] border border-[#222] rounded-xl p-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/50"></div>
        <h3 className="text-lg font-medium text-white mb-3">AI Business Context</h3>
        <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
          {lead.business_summary}
        </div>
      </div>

      {/* Section D: Meetings */}
      {lead.meetings.length > 0 && (
        <div className="bg-[#111] border border-[#222] rounded-xl p-6">
          <h3 className="text-lg font-medium text-white mb-4">Meetings</h3>
          <div className="grid gap-3">
            {lead.meetings.map(m => (
              <div key={m.id} className="flex items-center justify-between bg-[#1a1a1a] p-3 rounded-lg border border-[#333]">
                <div>
                  <p className="text-sm font-medium text-white">{m.date} at {formatTime(m.time)}</p>
                  {m.notes && <p className="text-xs text-gray-400 mt-1">{m.notes}</p>}
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    m.status === "Reserved" ? "bg-yellow-500/10 text-yellow-400" :
                    m.status === "Confirmed" ? "bg-green-500/10 text-green-400" : "bg-gray-500/10 text-gray-400"
                }`}>
                  {m.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section C: Conversation Timeline */}
      <div className="bg-[#111] border border-[#222] rounded-xl p-6">
        <h3 className="text-lg font-medium text-white mb-6">Interaction Timeline</h3>
        
        {lead.conversations.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No conversations recorded.</p>
        ) : (
          <div className="space-y-6">
            {lead.conversations.map((conv, idx) => {
              const isExpanded = expandedConv === conv.id;
              
              return (
                <div key={conv.id} className="relative pl-6 border-l-2 border-[#333]">
                  {/* Timeline dot */}
                  <div className="absolute w-3 h-3 bg-gray-600 rounded-full -left-[7px] top-1.5 ring-4 ring-[#111]"></div>
                  
                  <div 
                    className="bg-[#1a1a1a] border border-[#333] hover:border-[#444] rounded-lg p-4 cursor-pointer transition-colors"
                    onClick={() => setExpandedConv(isExpanded ? null : conv.id)}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div>
                        <span className="text-sm font-medium text-white mr-3">Session {lead.conversations.length - idx}</span>
                        <span className="text-xs text-gray-400">{formatDateTime(conv.started_at)}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-500">{formatDuration(conv.duration_seconds)}</span>
                        <span className={`text-xs px-2 py-1 rounded font-medium ${
                          conv.status === 'completed' ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'
                        }`}>
                          {conv.status}
                        </span>
                      </div>
                    </div>
                    
                    {/* Lazy load transcript expansion */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-[#333]">
                        {conv.summary && (
                          <div className="mb-4 text-sm text-gray-300 italic bg-black/50 p-3 rounded border border-[#222]">
                            "{conv.summary}"
                          </div>
                        )}
                        <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">Transcript</h4>
                        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                          {conv.messages.map((m, i) => (
                            <div key={i} className={`flex ${m.speaker === "user" ? "justify-end" : "justify-start"}`}>
                              <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                                m.speaker === "user"
                                  ? "bg-[hsl(var(--primary))]/10 text-green-300 border border-[hsl(var(--primary))]/20"
                                  : "bg-black text-gray-200 border border-[#222]"
                              }`}>
                                <p className="leading-relaxed">{m.content}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
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
        if (data && data.meetings) setMeetings(data.meetings);
        else setMeetings([]);
      })
      .catch((err) => {
        console.error(err);
        setMeetings([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 p-8">Loading meetings...</div>;
  if (meetings.length === 0) return <div className="text-gray-500 p-8 text-center bg-[#111] border border-[#222] rounded-xl mt-4">No meetings booked yet.</div>;

  return (
    <div className="overflow-x-auto bg-[#111] border border-[#222] rounded-xl mt-4">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[#222] text-gray-400 text-sm">
            <th className="py-4 pl-6 pr-4 font-medium">Date & Time</th>
            <th className="py-4 pr-4 font-medium">Lead Name</th>
            <th className="py-4 pr-4 font-medium">Email</th>
            <th className="py-4 pr-4 font-medium">Status</th>
            <th className="py-4 pr-4 font-medium">Notes</th>
            <th className="py-4 pr-6 font-medium">Booked At</th>
          </tr>
        </thead>
        <tbody>
          {meetings.map((m) => (
            <tr key={m.id} className="border-b border-[#1a1a1a]">
              <td className="py-4 pl-6 pr-4 text-sm text-white font-medium">
                {m.date || "—"} <span className="text-gray-400 font-normal ml-2">{formatTime(m.time)}</span>
              </td>
              <td className="py-4 pr-4 text-sm text-gray-300">{m.lead_name || "—"}</td>
              <td className="py-4 pr-4 text-sm text-blue-400">{m.email || "—"}</td>
              <td className="py-4 pr-4">
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    m.status === "Reserved" ? "bg-yellow-500/10 text-yellow-400" :
                    m.status === "Confirmed" ? "bg-green-500/10 text-green-400" :
                    m.status === "Completed" ? "bg-blue-500/10 text-blue-400" :
                    m.status === "No_Show" ? "bg-red-500/10 text-red-400" : "bg-gray-500/10 text-gray-400"
                  }`}
                >
                  {m.status}
                </span>
              </td>
              <td className="py-4 pr-4 text-sm text-gray-400 max-w-xs truncate">{m.notes || "—"}</td>
              <td className="py-4 pr-6 text-sm text-gray-500 whitespace-nowrap">{formatDateTime(m.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Main Dashboard ─── */
export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<"leads" | "meetings">("leads");
  const [selectedLead, setSelectedLead] = useState<number | null>(null);
  const [, navigate] = useLocation();

  // Auth guard
  useEffect(() => {
    if (!getToken()) navigate("/voice-agent/admin");
  }, [navigate]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("admin_token");
    navigate("/voice-agent/admin");
  }, [navigate]);

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Top Bar */}
      <header className="bg-[#0a0a0a] border-b border-[#222] px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <img src={logoFull} alt="PP5 Logo" className="h-8" />
          <span className="text-gray-500 text-sm border-l border-[#333] pl-3 ml-1">CRM Dashboard</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-400 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-[#1a1a1a]"
        >
          Logout
        </button>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Only show metrics and tabs if we are not inside a Lead Detail view */}
        {!selectedLead && (
          <>
            <DashboardMetrics />
            
            {/* Tab Navigation */}
            <div className="flex gap-2 mb-6 bg-[#111] border border-[#222] rounded-xl p-1.5 w-fit">
              <button
                onClick={() => setActiveTab("leads")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === "leads"
                    ? "bg-[hsl(var(--primary))] text-white shadow-lg shadow-[hsl(var(--primary))]/20"
                    : "text-gray-400 hover:text-white hover:bg-[#1a1a1a]"
                }`}
              >
                Leads & CRM
              </button>
              <button
                onClick={() => setActiveTab("meetings")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === "meetings"
                    ? "bg-[hsl(var(--primary))] text-white shadow-lg shadow-[hsl(var(--primary))]/20"
                    : "text-gray-400 hover:text-white hover:bg-[#1a1a1a]"
                }`}
              >
                Upcoming Meetings
              </button>
            </div>
          </>
        )}

        {/* Content */}
        {activeTab === "leads" && !selectedLead && (
          <LeadsView onSelect={setSelectedLead} />
        )}
        {activeTab === "leads" && selectedLead && (
          <LeadDetailView leadId={selectedLead} onBack={() => setSelectedLead(null)} />
        )}
        {activeTab === "meetings" && !selectedLead && <MeetingsView />}
      </div>
    </div>
  );
}
