import { useState, useEffect } from 'react';
import { X, ChevronRight, Check, Leaf, UploadCloud, ShieldCheck } from 'lucide-react';

const TOUR_STEPS = [
  {
    title: "Welcome to Breathe ESG",
    content: "This is a prototype enterprise climate ledger. Our goal is to ingest messy corporate data (SAP, Utility bills, Concur) and normalize it for audit.",
    actionText: "Next",
    icon: <Leaf size={48} color="var(--accent-primary)" />
  },
  {
    title: "1. Upload Sample Data",
    content: "Head over to the 'Data Ingestion' tab. We've provided 3 sample CSV files you can download directly from the page and upload to see the ingestion engine in action.",
    actionText: "Next",
    icon: <UploadCloud size={48} color="var(--accent-info, #3b82f6)" />
  },
  {
    title: "2. Review & Approve",
    content: "Once uploaded, go to the 'Review Records' tab. You can flag anomalies or switch your role to 'Admin' (top right) to officially approve the data and lock it for auditing!",
    actionText: "Got it!",
    icon: <ShieldCheck size={48} color="var(--accent-success, #10b981)" />
  }
];

const GuidedTour = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Check if they've already seen the tour
    const hasSeenTour = localStorage.getItem('breathe_esg_tour_completed');
    if (!hasSeenTour) {
      // Small delay to let the app load first
      const timer = setTimeout(() => setIsVisible(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      dismissTour();
    }
  };

  const dismissTour = () => {
    setIsVisible(false);
    localStorage.setItem('breathe_esg_tour_completed', 'true');
  };

  if (!isVisible) return null;

  return (
    <div className="tour-overlay animate-fade-in">
      <div className="tour-modal animate-slide-up" style={{ textAlign: 'center' }}>
        <button className="tour-close" onClick={dismissTour}>
          <X size={20} />
        </button>
        
        <div className="tour-body" style={{ padding: '40px 24px 32px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
            <div style={{ background: 'var(--bg-secondary)', padding: '20px', borderRadius: '50%', display: 'inline-flex' }}>
              {TOUR_STEPS[currentStep].icon}
            </div>
          </div>
          <h3 style={{ fontSize: '24px', marginBottom: '12px', fontWeight: 700 }}>{TOUR_STEPS[currentStep].title}</h3>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 auto', maxWidth: '350px' }}>
            {TOUR_STEPS[currentStep].content}
          </p>
        </div>

        <div className="tour-footer" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
          <button className="button" onClick={dismissTour} style={{ background: 'transparent', padding: '8px 12px', color: 'var(--text-secondary)' }}>
            Skip
          </button>
          
          <div className="tour-dots" style={{ display: 'flex', gap: '8px' }}>
            {TOUR_STEPS.map((_, idx) => (
              <div key={idx} className={`tour-dot ${idx === currentStep ? 'active' : ''}`} style={{ width: '8px', height: '8px', borderRadius: '50%', background: idx === currentStep ? 'var(--accent-primary)' : 'var(--border-color)', transition: 'all 0.3s' }} />
            ))}
          </div>

          <button className="button button-primary" onClick={handleNext} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}>
            {TOUR_STEPS[currentStep].actionText}
            {currentStep === TOUR_STEPS.length - 1 ? <Check size={16} /> : <ChevronRight size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default GuidedTour;
