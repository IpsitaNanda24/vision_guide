import React from 'react';
import { AlertCircle, Bell, Info, motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface OmniEvent {
  id: string;
  eventType: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  timestamp: Date;
}

interface EventAlertProps {
  event: OmniEvent;
  onClose: (id: string) => void;
}

const EventAlert: React.FC<EventAlertProps> = ({ event, onClose }) => {
  const getSeverityStyles = () => {
    switch (event.severity) {
      case 'critical':
        return "bg-red-50 border-red-200 text-red-700";
      case 'warning':
        return "bg-orange-50 border-orange-200 text-orange-700";
      default:
        return "bg-blue-50 border-blue-200 text-blue-700";
    }
  };

  const getIcon = () => {
    switch (event.severity) {
      case 'critical':
        return <AlertCircle className="shrink-0" size={24} />;
      case 'warning':
        return <Bell className="shrink-0" size={24} />;
      default:
        return <Info className="shrink-0" size={24} />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className={cn(
        "flex items-start gap-4 p-5 rounded-2xl border-2 shadow-lg mb-4 glass-card",
        getSeverityStyles()
      )}
    >
      <div className="mt-1">{getIcon()}</div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <h4 className="font-black uppercase tracking-tight text-sm mb-1">
            {event.eventType.replace('_', ' ')}
          </h4>
          <span className="text-[10px] font-bold opacity-50 uppercase">
            {event.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <p className="text-base font-bold leading-snug">{event.message}</p>
      </div>
      <button 
        onClick={() => onClose(event.id)}
        className="opacity-40 hover:opacity-100 transition-opacity p-1 font-black"
      >
        ✕
      </button>
    </motion.div>
  );
};

export default EventAlert;
