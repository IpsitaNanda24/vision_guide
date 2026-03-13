import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:3001';

export const useSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketIo = io(SOCKET_URL);

    socketIo.on('connect', () => {
      console.log('Connected to OmniSense Socket');
      setIsConnected(true);
    });

    socketIo.on('disconnect', () => {
      console.log('Disconnected from OmniSense Socket');
      setIsConnected(false);
    });

    setSocket(socketIo);

    return () => {
      socketIo.disconnect();
    };
  }, []);

  const emit = useCallback((event: string, data: any) => {
    if (socket) {
      socket.emit(event, data);
    }
  }, [socket]);

  const on = useCallback((event: string, callback: (...args: any[]) => void) => {
    if (socket) {
      socket.on(event, callback);
    }
  }, [socket]);

  const off = useCallback((event: string) => {
    if (socket) {
      socket.off(event);
    }
  }, [socket]);

  return { socket, isConnected, emit, on, off };
};
