import React from 'react';
import { Shield, UserPlus, Globe } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface HeaderProps {
  status: 'normal' | 'warning' | 'critical';
  seniorMode: boolean;
  setSeniorMode: (val: boolean) => void;
  language: string;
}

const Header: React.FC<HeaderProps> = ({ status, seniorMode, setSeniorMode, language }) => {
  return (
    <header className="flex items-center justify-between p-4 md:p-6 glass-card mt-4 mx-4">
      <div className="flex items-center gap-3">
        <div className={cn(
          "p-2 rounded-xl",
          status === 'normal' && "bg-primary/20 text-primary",
          status === 'warning' && "bg-orange-100 text-orange-500",
          status === 'critical' && "bg-accent/20 text-accent glow-accent"
        )}>
          <Shield size={24} strokeWidth={2.5} />
        </div>
        <h1 className="text-xl md:text-2xl font-black tracking-tight text-textMain">
          OmniSense
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-background rounded-full border border-borderLine text-sm font-medium">
          <Globe size={16} />
          <span>{language}</span>
        </div>

        <button
          onClick={() => setSeniorMode(!seniorMode)}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 font-bold",
            seniorMode 
              ? "bg-primary text-white shadow-lg glow-primary scale-105" 
              : "bg-white border border-borderLine text-textMain hover:bg-slate-50"
          )}
        >
          <UserPlus size={20} />
          <span className="hidden sm:inline">Senior Mode</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
