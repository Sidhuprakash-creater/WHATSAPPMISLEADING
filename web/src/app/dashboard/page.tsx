'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { Shield, TrendingUp, AlertOctagon, CheckCircle2, MessageSquare, ArrowUpRight, Activity } from 'lucide-react';

const MOCK_STATS = [
  { name: 'Mon', scans: 45, highRisk: 12 },
  { name: 'Tue', scans: 52, highRisk: 15 },
  { name: 'Wed', scans: 38, highRisk: 8 },
  { name: 'Thu', scans: 65, highRisk: 22 },
  { name: 'Fri', scans: 89, highRisk: 30 },
  { name: 'Sat', scans: 110, highRisk: 42 },
  { name: 'Sun', scans: 95, highRisk: 35 },
];

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-whatsapp-bg p-6 md:p-12 text-white">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black flex items-center gap-3">
              <Activity className="text-primary-whatsapp" /> System Oversight
            </h1>
            <p className="text-secondary text-sm">Real-time analysis metrics and misinformation trends.</p>
          </div>
          <div className="flex gap-2">
            <button className="bg-primary-whatsapp text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-primary-whatsapp/20">
              Export Report
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard icon={<MessageSquare />} label="Total Scans" value="1,284" trend="+12%" />
          <StatCard icon={<AlertOctagon color="#ef4444" />} label="High Risk Flagged" value="342" trend="+5%" />
          <StatCard icon={<CheckCircle2 color="#25d366" />} label="Verified Safe" value="894" trend="+8%" />
          <StatCard icon={<Shield />} label="Trust Score" value="94.2%" trend="+2%" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Main Activity Chart */}
          <div className="bg-whatsapp-surface border border-white/5 p-8 rounded-3xl shadow-xl">
            <div className="flex items-center justify-between mb-8">
              <h3 className="font-bold text-lg">Analysis Activity</h3>
              <div className="flex gap-4 text-xs font-bold text-secondary">
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-primary-whatsapp"/> Total</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500"/> High Risk</span>
              </div>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={MOCK_STATS}>
                  <defs>
                    <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00a884" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00a884" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#8696a0', fontSize: 12}} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#8696a0', fontSize: 12}} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#202c33', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area type="monotone" dataKey="scans" stroke="#00a884" strokeWidth={3} fillOpacity={1} fill="url(#colorScans)" />
                  <Area type="monotone" dataKey="highRisk" stroke="#ef4444" strokeWidth={2} fill="transparent" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Trends / List */}
          <div className="bg-whatsapp-surface border border-white/5 p-8 rounded-3xl shadow-xl flex flex-col">
            <h3 className="font-bold text-lg mb-6">Recent Alerts</h3>
            <div className="space-y-4 overflow-y-auto max-h-[300px] custom-scrollbar">
              <AlertItem 
                type="High Risk" 
                text="COVID vaccine containing nanochips forward..." 
                time="2m ago" 
              />
              <AlertItem 
                type="Medium Risk" 
                text="New rules for WhatsApp group admins..." 
                time="15m ago" 
              />
              <AlertItem 
                type="High Risk" 
                text="Click here for free 500GB 5G data..." 
                time="1h ago" 
              />
              <AlertItem 
                type="High Risk" 
                text="Government giving free laptops to students..." 
                time="3h ago" 
              />
            </div>
            <div className="mt-auto pt-6 text-center">
              <button className="text-primary-whatsapp font-bold text-sm hover:underline">
                View All History →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, trend }: { icon: React.ReactNode, label: string, value: string, trend: string }) {
  return (
    <div className="bg-whatsapp-surface border border-white/5 p-6 rounded-3xl hover:border-white/10 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 rounded-xl bg-white/5 text-secondary">
          {icon}
        </div>
        <div className="flex items-center gap-1 text-risk-low text-xs font-bold bg-risk-low/10 px-2 py-0.5 rounded-full">
          <TrendingUp size={12} /> {trend}
        </div>
      </div>
      <div>
        <p className="text-secondary text-xs uppercase tracking-widest font-bold mb-1">{label}</p>
        <h4 className="text-3xl font-black">{value}</h4>
      </div>
    </div>
  );
}

function AlertItem({ type, text, time }: { type: string, text: string, time: string }) {
  const isHigh = type === 'High Risk';
  return (
    <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-transparent hover:border-white/10 transition-all cursor-pointer">
      <div className="flex items-center gap-4">
        <div className={`w-2 h-10 rounded-full ${isHigh ? 'bg-risk-high' : 'bg-risk-medium'}`} />
        <div>
          <p className="text-sm font-bold text-white line-clamp-1">{text}</p>
          <p className={`text-[10px] font-black uppercase ${isHigh ? 'text-risk-high' : 'text-risk-medium'}`}>{type}</p>
        </div>
      </div>
      <div className="text-xs text-secondary font-mono">
        {time}
      </div>
    </div>
  );
}
