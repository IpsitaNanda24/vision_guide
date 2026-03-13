import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import ModeSelector from '../components/ModeSelector';
import ListenerCard from '../components/ListenerCard';
import EventAlert, { OmniEvent } from '../components/EventAlert';
import SOSButton from '../components/SOSButton';
import { AnimatePresence, motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const [mode, setMode] = useState<'vision' | 'audio'>('audio');
  const [isListening, setIsListening] = useState(false);
  const [seniorMode, setSeniorMode] = useState(false);
  const [events, setEvents] = useState<OmniEvent[]>([]);
  const [status, setStatus] = useState<'normal' | 'warning' | 'critical'>('normal');

  // Handle Senior Mode body class
  useEffect(() => {
    if (seniorMode) {
      document.body.classList.add('senior-mode');
    } else {
      document.body.classList.remove('senior-mode');
    }
  }, [seniorMode]);

  // Mock event generator
  const addMockEvent = () => {
    const mockEvents: Partial<OmniEvent>[] = [
      { eventType: "baby_crying", message: "A baby is crying nearby. Please check.", severity: "warning" },
      { eventType: "smoke_alarm", message: "Smoke alarm detected! Exit immediately.", severity: "critical" },
      { eventType: "doorbell", message: "Someone is at the door.", severity: "info" },
      { eventType: "car_approaching", message: "A vehicle is approaching from your left.", severity: "warning" }
    ];
    
    const randomEvent = mockEvents[Math.floor(Math.random() * mockEvents.length)];
    const newEvent: OmniEvent = {
      ...randomEvent as OmniEvent,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date()
    };
    
    setEvents(prev => [newEvent, ...prev].slice(0, 5));
    if (newEvent.severity === 'critical') setStatus('critical');
    else if (newEvent.severity === 'warning' && status !== 'critical') setStatus('warning');
  };

  const toggleListening = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Simulate hearing something after 3 seconds
      setTimeout(addMockEvent, 3000);
    }
  };

  const removeEvent = (id: string) => {
    setEvents(prev => {
      const filtered = prev.filter(e => e.id !== id);
      if (filtered.length === 0) setStatus('normal');
      else if (!filtered.some(e => e.severity === 'critical')) {
        setStatus(filtered.some(e => e.severity === 'warning') ? 'warning' : 'normal');
      }
      return filtered;
    });
  };

  return (
    <div className="min-h-screen max-w-2xl mx-auto flex flex-col relative pb-24">
      <Header 
        status={status} 
        seniorMode={seniorMode} 
        setSeniorMode={setSeniorMode} 
        language="English" 
      />
      
      <main className="flex-1 px-4">
        <ModeSelector mode={mode} setMode={setMode} />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <ListenerCard 
            mode={mode} 
            isListening={isListening} 
            onToggle={toggleListening} 
          />
        </motion.div>

        <section className="mt-8">
          <AnimatePresence>
            {events.map(event => (
              <EventAlert 
                key={event.id} 
                event={event} 
                onClose={removeEvent} 
              />
            ))}
          </AnimatePresence>
          
          {events.length === 0 && !isListening && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              className="text-center py-12 text-slate-400 font-bold uppercase tracking-widest text-xs"
            >
              No active events
            </motion.div>
          )}
        </section>
      </main>

      {/* Start Listening Button (Bottom Anchored on Mobile) */}
      <div className="fixed bottom-6 right-6 z-50">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleListening}
          className={cn(
            "flex items-center gap-3 px-8 py-4 rounded-full font-black text-lg shadow-2xl transition-all duration-500",
            isListening 
              ? "bg-white text-primary border-2 border-primary" 
              : "bg-primary text-white glow-primary"
          )}
        >
          {isListening ? (
            <>
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full"
              />
              <span>Listening...</span>
            </>
          ) : (
            <span>Start Listening</span>
          )}
        </motion.button>
      </div>

      <SOSButton />
    </div>
  );
};

// Simple helper function duplicated here for brevity in single file implementation
function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}

export default Dashboard;
