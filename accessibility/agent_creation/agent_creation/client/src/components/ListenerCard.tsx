import React from 'react';
import { Mic, Camera, motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ListenerCardProps {
  mode: 'vision' | 'audio';
  isListening: boolean;
  onToggle: () => void;
  statusText?: string;
}

const ListenerCard: React.FC<ListenerCardProps> = ({ mode, isListening, onToggle, statusText }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 mt-12 mb-8">
      <div className="relative">
        {/* Pulsing Background Rings */}
        <AnimatePresence>
          {isListening && (
            <>
              <motion.div
                className="absolute inset-0 bg-primary/20 rounded-full z-0"
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 2, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
              />
              <motion.div
                className="absolute inset-0 bg-primary/10 rounded-full z-0"
                initial={{ scale: 1, opacity: 0.3 }}
                animate={{ scale: 2.5, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
              />
            </>
          )}
        </AnimatePresence>

        {/* Main Interaction Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onToggle}
          className={cn(
            "relative z-10 w-48 h-48 rounded-full flex flex-col items-center justify-center transition-all duration-500",
            isListening 
              ? "bg-primary text-white shadow-[0_0_40px_rgba(108,124,255,0.6)]" 
              : "bg-white border-4 border-slate-100 text-primary shadow-xl hover:shadow-2xl"
          )}
        >
          {mode === 'audio' ? (
            <Mic size={64} className={cn("transition-transform duration-500", isListening && "scale-110")} />
          ) : (
            <Camera size={64} className={cn("transition-transform duration-500", isListening && "scale-110")} />
          )}
          
          <span className="mt-4 font-black uppercase tracking-widest text-xs">
            {isListening ? "Listening..." : "Tap to Start"}
          </span>
        </motion.button>
      </div>

      <div className="mt-12 text-center max-w-sm">
        <h2 className="text-2xl font-black text-textMain mb-2">
          Environmental {mode === 'audio' ? 'Listener' : 'Vision'}
        </h2>
        <p className="text-slate-500 font-medium leading-relaxed">
          {statusText || `Tap the button to analyze ${mode === 'audio' ? 'sounds' : 'your surroundings'} and get real-time guidance.`}
        </p>
      </div>
    </div>
  );
};

export default ListenerCard;
