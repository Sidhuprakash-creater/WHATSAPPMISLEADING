'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Info, ExternalLink, ShieldAlert, BarChart3, Fingerprint } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface VerdictCardProps {
  result: any;
  onClose?: () => void;
}

export default function VerdictCard({ result, onClose }: VerdictCardProps) {
  const verdict = result.final_verdict?.verdict || 'Unknown';
  const confidence = result.final_verdict?.confidence_score || 0;
  const reasons = result.final_verdict?.reasons || [];
  
  const isHigh = verdict === 'High Risk';
  const isLow = verdict === 'Low Risk';

  const chartData = [
    { name: 'Confidence', value: confidence },
    { name: 'Remaining', value: 100 - confidence },
  ];

  const COLORS = [
    isHigh ? '#ef4444' : isLow ? '#25d366' : '#ffbc2d',
    'rgba(255,255,255,0.05)'
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-whatsapp-surface border border-white/10 rounded-3xl overflow-hidden shadow-2xl max-w-2xl w-full"
    >
      {/* Header Banner */}
      <div className={`p-6 flex items-center justify-between ${
        isHigh ? 'bg-risk-high/20' : isLow ? 'bg-risk-low/20' : 'bg-risk-medium/20'
      }`}>
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-2xl ${isHigh ? 'bg-risk-high' : isLow ? 'bg-risk-low' : 'bg-risk-medium'}`}>
            {isHigh ? <ShieldAlert size={28} className="text-white" /> : <CheckCircle2 size={28} className="text-white" />}
          </div>
          <div>
            <h2 className="text-2xl font-black text-white">{verdict.toUpperCase()}</h2>
            <p className="text-sm text-white/70">Analysis Confidence: {confidence}%</p>
          </div>
        </div>
        
        {onClose && (
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-white/50 hover:text-white">
            ✕
          </button>
        )}
      </div>

      <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8 text-white">
        {/* Left Col: Stats & Visuals */}
        <div className="space-y-6">
          <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-4 flex items-center gap-2">
              <BarChart3 size={14} /> Match Probability
            </h3>
            <div className="h-40 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={0}
                    dataKey="value"
                    stroke="none"
                    startAngle={90}
                    endAngle={-270}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black">{confidence}%</span>
                <span className="text-[10px] text-secondary">CERTAINTY</span>
              </div>
            </div>
          </div>

          <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-3 flex items-center gap-2">
              <Fingerprint size={14} /> Analysis Metadata
            </h3>
            <div className="space-y-2">
              <MetaRow label="Content Type" value={result.input_type || 'Text'} />
              <MetaRow label="Analyzers Run" value="ML, LLM, FactCheck" />
              <MetaRow label="Scan Time" value={`${result.process_time_ms || 120}ms`} />
            </div>
          </div>
        </div>

        {/* Right Col: Reasoning & Logic */}
        <div className="space-y-6">
          <div>
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-4 flex items-center gap-2">
              <Info size={14} /> Key Reasoning Factor
            </h3>
            <div className="space-y-3">
              {reasons.map((reason: string, idx: number) => (
                <div key={idx} className="flex gap-3 items-start group">
                  <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary-whatsapp group-hover:scale-150 transition-transform" />
                  <p className="text-sm text-white/90 leading-snug">{reason}</p>
                </div>
              ))}
            </div>
          </div>

          {result.url_scan && (
            <div className="pt-4 border-t border-white/10">
              <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-3">Security Flags</h3>
              <div className="flex gap-2">
                <Badge text="WHOIS Checked" color="green" />
                <Badge text="Anti-Phishing" color="blue" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer CTA */}
      <div className="bg-white/5 p-4 flex justify-between items-center border-t border-white/5">
        <p className="text-[10px] text-secondary font-medium">SCAN ID: {result.scan_id || 'LOCAL-' + Date.now()}</p>
        <button className="flex items-center gap-2 text-primary-whatsapp font-bold text-xs hover:bg-primary-whatsapp/10 px-4 py-2 rounded-full transition-all">
          <ExternalLink size={14} /> SOURCE VERIFICATION
        </button>
      </div>
    </motion.div>
  );
}

function MetaRow({ label, value }: { label: string, value: string }) {
  return (
    <div className="flex justify-between text-[11px]">
      <span className="text-secondary">{label}</span>
      <span className="text-white font-mono">{value}</span>
    </div>
  );
}

function Badge({ text, color }: { text: string, color: string }) {
  return (
    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border border-white/10 bg-white/5`}>
      {text}
    </span>
  );
}
