import ChatInterface from '@/components/ChatInterface';
import { Shield, Zap, Search, Globe } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-whatsapp-bg flex flex-col items-center p-4 md:p-8">
      {/* Hero Section */}
      <div className="w-full max-w-5xl mb-8 flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="flex-1 space-y-4 text-center md:text-left">
          <div className="inline-flex items-center space-x-2 bg-primary-whatsapp/10 text-primary-whatsapp px-3 py-1 rounded-full text-sm font-bold border border-primary-whatsapp/20">
            <Shield size={16} />
            <span>AI-Powered Verification</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight">
            Spot the <span className="text-primary-whatsapp">Fake.</span> <br />
            Share the <span className="text-risk-low">Truth.</span>
          </h1>
          <p className="text-secondary text-lg max-w-xl">
            The world's first multi-modal misinformation detection system designed specifically for WhatsApp forwards.
            Paste text, links, or upload images to verify them instantly.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center md:justify-start pt-2">
            <FeatureBadge icon={<Zap size={14} />} text="Instant ML Scan" />
            <FeatureBadge icon={<Search size={14} />} text="Fact-Check Search" />
            <FeatureBadge icon={<Globe size={14} />} text="Regional Context" />
          </div>
        </div>

        {/* Chat Bot Preview Container */}
        <div className="w-full max-w-md">
          <ChatInterface />
        </div>
      </div>

      {/* Footer Info */}
      <div className="w-full max-w-5xl mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <InfoCard 
          title="3-Tier Reasoning" 
          description="We use Logistic Regression for speed, Claude 3.5 for reasoning, and FAISS for semantic fact-checking."
        />
        <InfoCard 
          title="Regional Support" 
          description="Native support for Hindi, Hinglish, and Odia to catch localized viral misinformation."
        />
        <InfoCard 
          title="Privacy First" 
          description="Your messages are analyzed in real-time and never stored permanently without your consent."
        />
      </div>

      <p className="mt-16 text-secondary text-xs opacity-50 uppercase tracking-widest font-bold">
        Powered by Google Gemini & Anthropic Claude
      </p>
    </main>
  );
}

function FeatureBadge({ icon, text }: { icon: React.ReactNode, text: string }) {
  return (
    <div className="flex items-center space-x-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg text-xs font-semibold text-white/80">
      {icon}
      <span>{text}</span>
    </div>
  );
}

function InfoCard({ title, description }: { title: string, description: string }) {
  return (
    <div className="bg-whatsapp-surface/50 border border-white/5 p-6 rounded-2xl hover:border-primary-whatsapp/30 transition-all group">
      <h3 className="text-white font-bold mb-2 group-hover:text-primary-whatsapp transition-colors">{title}</h3>
      <p className="text-secondary text-sm leading-relaxed">{description}</p>
    </div>
  );
}
