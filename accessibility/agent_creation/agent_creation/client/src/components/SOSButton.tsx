import React from 'react';
import { motion } from 'framer-motion';

const SOSButton: React.FC = () => {
  const triggerEmergency = () => {
    alert("Emergency Workflow Triggered! Contacting emergency services...");
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1, rotate: 5 }}
      whileTap={{ scale: 0.9 }}
      onClick={triggerEmergency}
      className="fixed bottom-6 left-6 w-16 h-16 bg-accent text-white rounded-full shadow-[0_0_30px_rgba(255,107,107,0.5)] flex items-center justify-center font-black text-xl z-50 transition-all duration-300 hover:shadow-[0_0_50px_rgba(255,107,107,0.8)]"
      title="SOS Emergency"
    >
      SOS
    </motion.button>
  );
};

export default SOSButton;
