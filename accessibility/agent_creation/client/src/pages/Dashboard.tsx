import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import ModeSelector from '../components/ModeSelector';
import ListenerCard from '../components/ListenerCard';
import EventAlert from '../components/EventAlert';
import SOSButton from '../components/SOSButton';
import { AnimatePresence, motion } from 'framer-motion';
import { useSocket } from '../hooks/useSocket';
import { OmniEvent } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

const Dashboard: React.FC = () => {
  const [mode, setMode] = useState<'vision' | 'audio'>('audio');
  const [isListening, setIsListening] = useState(false);
  const [seniorMode, setSeniorMode] = useState(false);
  const [events, setEvents] = useState<OmniEvent[]>([]);
  const [status, setStatus] = useState<'normal' | 'warning' | 'critical'>('normal');
  
  const { on, off, isConnected } = useSocket();

  useEffect(() => {
    on('environment_event', (eventData: any) => {
      const newEvent: OmniEvent = {
        ...eventData.data,
        timestamp: new Date(eventData.data.timestamp || Date.now())
      };
      
      setEvents(prev => [newEvent, ...prev].slice(0, 5));
      updateSystemStatus(newEvent.severity);
    });

    return () => off('environment_event');
  }, [on, off]);

  useEffect(() => {
    if (seniorMode) {
      document.body.classList.add('senior-mode');
    } else {
      document.body.classList.remove('senior-mode');
    }
  }, [seniorMode]);

  const updateSystemStatus = (severity: string) => {
    if (severity === 'critical') setStatus('critical');
    else if (severity === 'warning' && status !== 'critical') setStatus('warning');
  };

  const toggleListening = async () => {
    try {
      const endpoint = isListening ? '/api/listen/stop' : '/api/listen/start';
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, seniorMode })
      });

      if (response.ok) {
        setIsListening(!isListening);
      }
    } catch (error) {
      console.error("Failed to toggle listening:", error);
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
        <div className="flex justify-center mt-2">
          <span className={`text-[10px] font-bold uppercase tracking-widest ${isConnected ? 'text-green-500' : 'text-red-400'}`}>
            {isConnected ? '● System Connected' : '○ System Offline'}
          </span>
        </div>

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

      <div className="fixed bottom-6 right-6 z-50">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleListening}
          className={`flex items-center gap-3 px-8 py-4 rounded-full font-black text-lg shadow-2xl transition-all duration-500 ${
            isListening 
              ? "bg-white text-primary border-2 border-primary" 
              : "bg-primary text-white glow-primary"
          }`}
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

export default Dashboard;
