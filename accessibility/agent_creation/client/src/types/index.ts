export interface OmniEvent {
  id: string;
  eventType: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  timestamp: Date;
}

export type AppMode = 'vision' | 'audio';
