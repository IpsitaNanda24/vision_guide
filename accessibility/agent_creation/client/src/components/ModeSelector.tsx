import React from 'react';
import { Eye, Mic } from 'lucide-react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ModeSelectorProps {
  mode: 'vision' | 'audio';
  setMode: (mode: 'vision' | 'audio') => void;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({ mode, setMode }) => {
  return (
    <div className="flex justify-center mt-8 px-4">
      <div className="relative flex bg-slate-200/50 p-1.5 rounded-2xl w-full max-w-md backdrop-blur-sm border border-white/50">
        <motion.div
          className="absolute h-[calc(100%-12px)] top-1.5 bottom-1.5 bg-white rounded-xl shadow-md z-0"
          initial={false}
          animate={{
            left: mode === 'vision' ? '6px' : 'calc(50% + 3px)',
            width: 'calc(50% - 9px)',
          }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />

        <button
          onClick={() => setMode('vision')}
          className={cn(
            "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 font-bold transition-colors duration-300",
            mode === 'vision' ? "text-primary" : "text-slate-500 hover:text-slate-700"
          )}
        >
          <Eye size={20} />
          <span>Vision</span>
        </button>

        <button
          onClick={() => setMode('audio')}
          className={cn(
            "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 font-bold transition-colors duration-300",
            mode === 'audio' ? "text-primary" : "text-slate-500 hover:text-slate-700"
          )}
        >
          <Mic size={20} />
          <span>Audio</span>
        </button>
      </div>
    </div>
  );
};

export default ModeSelector;
