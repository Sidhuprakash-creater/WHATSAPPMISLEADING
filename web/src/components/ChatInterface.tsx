'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Image as ImageIcon, Link as LinkIcon, AlertCircle, CheckCircle2, MoreVertical, Smartphone } from 'lucide-react';
import { useChatStore, Message } from '@/lib/store';
import { motion, AnimatePresence } from 'framer-motion';
import VerdictCard from './VerdictCard';

export default function ChatInterface() {
  const { messages, addMessage, isAnalyzing, setAnalyzing, updateMessage } = useChatStore();
  const [inputText, setInputText] = useState('');
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim() || isAnalyzing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText,
      timestamp: Date.now(),
    };

    addMessage(userMessage);
    setInputText('');
    setAnalyzing(true);

    const assistantId = (Date.now() + 1).toString();
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      progressStep: { step: 'initializing', message: 'Starting analysis...', progress: 10 }
    });

    try {
      // 1. Determine Content Type
      const isUrl = inputText.startsWith('http://') || inputText.startsWith('https://');
      const contentType = isUrl ? 'url' : 'text';

      // 2. Call Analysis API
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content_type: contentType,
          text: userMessage.content,
          session_id: 'web-session-1'
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Analysis failed');
      }
      const result = await response.json();

      // 3. Update Store & Message
      useChatStore.getState().recordAnalysis(result);
      
      updateMessage(assistantId, {
        content: result.final_verdict?.verdict === 'High Risk' 
          ? `🚨 ANALYSIS COMPLETE: This content carries a ${result.final_verdict?.verdict}.` 
          : `✅ ANALYSIS COMPLETE: This content is ${result.final_verdict?.verdict}.`,
        analysisResult: result,
        progressStep: undefined
      });

    } catch (error) {
      updateMessage(assistantId, {
        content: 'Sorry, I encountered an error while analyzing that content. Please try again.',
        progressStep: undefined
      });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col h-[90vh] bg-whatsapp-bg rounded-2xl shadow-2xl border border-white/5 overflow-hidden">
      {/* Header */}
      <div className="bg-whatsapp-surface p-4 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-primary-whatsapp flex items-center justify-center text-white font-bold">
            M
          </div>
          <div>
            <h2 className="text-white font-semibold">MisLEADING Bot</h2>
            <p className="text-xs text-secondary italic">{isAnalyzing ? 'Analyzing...' : 'Online'}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-secondary">
          <Smartphone size={18} />
          <MoreVertical size={18} />
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-[url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')] bg-repeat opacity-90"
      >
        <AnimatePresence>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] rounded-xl p-3 shadow-md relative ${
                m.role === 'user' 
                  ? 'bg-whatsapp-bubble-me text-white rounded-tr-none' 
                  : 'bg-whatsapp-bubble-them text-white rounded-tl-none'
              }`}>
                {m.content && <p className="text-sm select-text whitespace-pre-wrap">{m.content}</p>}
                
                {m.progressStep && (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-secondary animate-pulse">{m.progressStep.message}</p>
                    <div className="w-full bg-white/10 h-1 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${m.progressStep.progress}%` }}
                        className="bg-primary-whatsapp h-full"
                      />
                    </div>
                  </div>
                )}

                {m.analysisResult && (
                  <div className="mt-3 pt-3 border-t border-white/10">
                    <VerdictSummary 
                      result={m.analysisResult} 
                      onViewFull={() => setSelectedResult(m.analysisResult)} 
                    />
                  </div>
                )}

                <div className="flex justify-end mt-1">
                  <span className="text-[10px] text-white/50">
                    {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <div className="p-3 bg-whatsapp-surface flex items-center space-x-2">
        <button className="p-2 text-secondary hover:text-white transition-colors">
          <ImageIcon size={22} />
        </button>
        <div className="flex-1 relative">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message or paste a link..."
            className="w-full bg-[#2a3942] text-white rounded-full py-2.5 px-4 outline-none placeholder:text-secondary text-sm"
          />
        </div>
        <button 
          onClick={handleSend}
          disabled={!inputText.trim() || isAnalyzing}
          className={`p-3 rounded-full transition-all ${
            !inputText.trim() || isAnalyzing 
              ? 'bg-[#2a3942] text-secondary' 
              : 'bg-primary-whatsapp text-white scale-110 shadow-lg'
          }`}
        >
          <Send size={20} />
        </button>
      </div>

      {/* Modal Overlay for Full Report */}
      <AnimatePresence>
        {selectedResult && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <VerdictCard 
              result={selectedResult} 
              onClose={() => setSelectedResult(null)} 
            />
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function VerdictSummary({ result, onViewFull }: { result: any, onViewFull: () => void }) {
  const verdict = result.final_verdict?.verdict || 'Unknown';
  const confidence = result.final_verdict?.confidence_score || 0;
  
  const isHigh = verdict === 'High Risk';
  const isLow = verdict === 'Low Risk';

  return (
    <div className={`p-3 rounded-lg border flex flex-col gap-2 ${
      isHigh ? 'bg-risk-high/10 border-risk-high/20' : 
      isLow ? 'bg-risk-low/10 border-risk-low/20' : 
      'bg-risk-medium/10 border-risk-medium/20'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isHigh ? <AlertCircle className="text-risk-high" size={18} /> : <CheckCircle2 className="text-risk-low" size={18} />}
          <span className={`font-bold text-sm ${isHigh ? 'text-risk-high' : isLow ? 'text-risk-low' : 'text-risk-medium'}`}>
            {verdict}
          </span>
        </div>
        <span className="text-xs font-mono text-white/70">{confidence}% Match</span>
      </div>
      
      {result.final_verdict?.reasons && (
        <ul className="text-[11px] text-white/80 list-disc list-inside space-y-1">
          {result.final_verdict.reasons.slice(0, 3).map((r: string, i: number) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}

      <button 
        onClick={onViewFull}
        className="mt-2 text-[10px] text-primary-whatsapp font-bold hover:underline self-end"
      >
        VIEW FULL REPORT →
      </button>
    </div>
  );
}
