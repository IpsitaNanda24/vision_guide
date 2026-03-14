import React, { useState, useEffect, useRef } from 'react';
import { Camera, Mic, Shield, AlertTriangle, Play, Square, Heart, Info, Activity, History } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAccessibility } from './hooks/useAccessibility';
import { Layout } from './components/layout/Layout';
import { StatusCard } from './components/dashboard/StatusCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';

const App = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [isRecording, setIsRecording] = useState(false);
  const [audioResult, setAudioResult] = useState(null);
  const [activeAlert, setActiveAlert] = useState(null);
  const [eventHistory, setEventHistory] = useState([]);

  const {
    safetyLevel, isAnalyzing, speak,
    videoRef, canvasRef, captureAndAnalyze, analyzeAudio, mediaStreamRef,
    startVoiceCommands, stopVoiceCommands, voiceStatus,
    seniorMode, setSeniorMode, language, setLanguage,
    hasStarted, handleStartSystems, handleStopSystems,
    isLiveStreaming, startLiveStream, stopLiveStream,
    isScanning, autoGuidance, setAutoGuidance
  } = useAccessibility();

  // Voice command sync based on view
  useEffect(() => {
    if (hasStarted && (currentView === 'vision' || currentView === 'dashboard')) {
      startVoiceCommands();
    } else {
      stopVoiceCommands();
    }
  }, [hasStarted, currentView, startVoiceCommands, stopVoiceCommands]);

  const addEventToHistory = (event) => {
    setEventHistory(prev => [event, ...prev].slice(0, 10)); // Keep last 10
  };

  const handleAudioListen = async () => {
    if (isRecording || isAnalyzing) return;

    if (!mediaStreamRef.current) {
      speak("Microphone not available. Please allow microphone access.");
      return;
    }

    const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
    const recorder = new MediaRecorder(mediaStreamRef.current, { mimeType });
    const chunks = [];
    setIsRecording(true);
    setAudioResult(null);

    recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
    recorder.onstop = async () => {
      const blob = new Blob(chunks, { type: mimeType });
      const result = await analyzeAudio(blob);
      try {
        const blob = new Blob(chunks, { type: mimeType });
        const result = await analyzeAudio(blob);

        if (result) {
          setAudioResult(result);
          addEventToHistory({
            time: new Date().toLocaleTimeString(),
            type: 'Audio',
            detail: result.sound_event,
            status: result.urgency === 'Critical' ? 'Danger' : 'Info'
          });

          if (result.urgency === 'Critical' || result.urgency === 'Caution') {
            setActiveAlert({
              title: result.sound_event,
              message: result.guidance,
              type: result.urgency
            });
            // Auto-clear alert after 8 seconds
            setTimeout(() => setActiveAlert(null), 8000);
          }
        }
      } catch (err) {
        console.error("Audio analysis failed:", err);
      } finally {
        setIsRecording(false);
      }
    };

    recorder.start(100);
    setTimeout(() => {
      if (recorder.state === 'recording') {
        recorder.stop();
      }
    }, 4000);
  };

  // Continuous Audio Monitoring
  useEffect(() => {
    if (!hasStarted || currentView !== 'audio') return;
    const monitorInterval = setInterval(() => {
      if (!isRecording && !isAnalyzing) {
        handleAudioListen();
      }
    }, 20000);
    return () => clearInterval(monitorInterval);
  }, [hasStarted, currentView, isRecording, isAnalyzing]);

  // Continuous Vision Guidance
  useEffect(() => {
    if (!hasStarted || currentView !== 'vision' || !autoGuidance || isLiveStreaming) return;
    const visionInterval = setInterval(() => {
      captureAndAnalyze("Provide a safety check and navigation prompt.");
      addEventToHistory({
        time: new Date().toLocaleTimeString(),
        type: 'Vision',
        detail: 'Auto-scan completed',
        status: 'Info'
      });
    }, 60000);
    return () => clearInterval(visionInterval);
  }, [hasStarted, currentView, autoGuidance, isLiveStreaming]);

  const handleSOSTrigger = () => {
    speak("SOS Triggered. Emergency protocol initiated.");
    addEventToHistory({
      time: new Date().toLocaleTimeString(),
      type: 'Emergency',
      detail: 'SOS Triggered',
      status: 'Danger'
    });
    alert("SOS TRIGGERED! Emergency contacts would be notified.");
  };

  if (!hasStarted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md shadow-lg border-primary/20">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto bg-primary/10 p-4 rounded-full w-20 h-20 flex items-center justify-center">
              <Shield className="w-10 h-10 text-primary" />
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight bg-gradient-to-br from-primary to-blue-600 bg-clip-text text-transparent">
              OmniSense
            </CardTitle>
            <CardDescription className="text-base">
              System Initialization required. We need access to your camera and microphone to provide real-time accessibility guidance.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center pt-4">
            <Button size="lg" className="w-full text-lg h-14" onClick={handleStartSystems}>
              Initialize Systems
            </Button>
          </CardContent>
          <CardFooter className="justify-center text-sm text-muted-foreground flex items-center space-x-2">
            <Info className="w-4 h-4" />
            <span>Privacy First: All processing is secure and transparent.</span>
          </CardFooter>
        </Card>
      </div>
    );
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
        <p className="text-muted-foreground">Monitor your surroundings and system status.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatusCard
          title="Safety Level"
          value={safetyLevel}
          icon={Shield}
          description="Current environment assessment"
          className={safetyLevel === 'Safe' ? 'border-green-500/50' : 'border-yellow-500/50'}
        />
        <StatusCard
          title="Active Mode"
          value={currentView.charAt(0).toUpperCase() + currentView.slice(1)}
          icon={Activity}
          description="Currently focused sensory mode"
        />
        <StatusCard
          title="Voice Command"
          value={voiceStatus}
          icon={Mic}
          description="Voice recognition system status"
        />
        <StatusCard
          title="Senior Mode"
          value={seniorMode ? "Active" : "Inactive"}
          icon={Heart}
          description="Wellness and companion features"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
            <CardDescription>Latest sensory detections and system logs.</CardDescription>
          </CardHeader>
          <CardContent>
            {eventHistory.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Event</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {eventHistory.map((event, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{event.time}</TableCell>
                      <TableCell>{event.type}</TableCell>
                      <TableCell>{event.detail}</TableCell>
                      <TableCell>
                        <Badge variant={event.status === 'Danger' ? 'destructive' : 'default'}>
                          {event.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                <History className="h-10 w-10 mb-4 opacity-50" />
                <p>No recent events recorded.</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Essential accessibility controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              className="w-full h-16 text-lg justify-start px-6"
              variant="outline"
              onClick={() => setCurrentView('vision')}
            >
              <Camera className="mr-4 h-6 w-6" />
              Start Vision Scan
            </Button>
            <Button
              className="w-full h-16 text-lg justify-start px-6"
              variant="outline"
              onClick={() => setCurrentView('audio')}
            >
              <Mic className="mr-4 h-6 w-6" />
              Start Audio Guard
            </Button>
            <Button
              className="w-full h-16 text-lg justify-start px-6 bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={handleSOSTrigger}
            >
              <AlertTriangle className="mr-4 h-6 w-6" />
              Emergency SOS
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderVision = () => (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Vision Stream</h2>
        <p className="text-muted-foreground">Real-time scene analysis and navigation assistance.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3 flex-1 min-h-0">
        <Card className="md:col-span-2 flex flex-col overflow-hidden relative">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between">
              <span>Camera Feed</span>
              {isLiveStreaming && <Badge className="bg-red-500 animate-pulse">LIVE</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0 relative bg-black flex items-center justify-center">
            <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover opacity-80" />
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {(isAnalyzing || isScanning) && (
              <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center z-10 text-white">
                <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                <span className="text-lg font-medium">{isScanning ? 'Scanning Environment...' : 'Analyzing Frame...'}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Vision Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 flex-1">
            <Button
              className="w-full h-12"
              variant={isLiveStreaming ? "destructive" : "default"}
              onClick={isLiveStreaming ? stopLiveStream : startLiveStream}
            >
              {isLiveStreaming ? <Square className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
              {isLiveStreaming ? "Stop Live Session" : "Start Live Session"}
            </Button>

            <Button
              className="w-full"
              variant="outline"
              onClick={() => {
                setAutoGuidance(!autoGuidance);
                speak(autoGuidance ? "Auto guidance disabled." : "Auto guidance enabled.");
              }}
              disabled={isLiveStreaming}
            >
              <Shield className="mr-2 h-4 w-4" />
              {autoGuidance ? "Stop Auto-Guidance" : "Enable Auto-Guidance"}
            </Button>

            <Button
              className="w-full"
              variant="secondary"
              onClick={() => {
                captureAndAnalyze();
                addEventToHistory({
                  time: new Date().toLocaleTimeString(),
                  type: 'Vision',
                  detail: 'Manual check requested',
                  status: 'Info'
                });
              }}
              disabled={isAnalyzing || isLiveStreaming || isScanning}
            >
              <Camera className="mr-2 h-4 w-4" />
              Check Surroundings Now
            </Button>
          </CardContent>
          <CardFooter className="bg-muted/50 text-sm text-muted-foreground flex flex-col items-start space-y-2 p-4">
            <div className="flex items-center"><Mic className="mr-2 h-4 w-4" /> Voice: {voiceStatus}</div>
            <div className="flex items-center"><Info className="mr-2 h-4 w-4" /> Say "Describe" for full update.</div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );

  const AudioPane = ({ audioStatus, onListen, isAnalyzing, isRecording, audioResult, isLiveStreaming, startLiveStream, stopLiveStream }) => (
    <div className="glass-morphism pane-card audio-hub">
      <div className="mic-viz-container">
        <div className={`mic-circle ${isRecording || isAnalyzing || isLiveStreaming ? 'active' : ''}`}>
          <Mic size={48} className={isRecording || isLiveStreaming ? 'animate-pulse' : ''} />
        </div>
      </div>
      <div className="audio-meta">
        <h3>{isRecording ? 'Recording...' : isAnalyzing ? 'Analyzing...' : isLiveStreaming ? 'Real-time Active' : audioStatus}</h3>
        <p className="text-muted">
          {isRecording ? 'Listening for 4 seconds...' : isLiveStreaming ? 'Streaming live audio to Gemini...' : 'Tap to analyze environmental sounds'}
        </p>
      </div>
      {audioResult && !isLiveStreaming && (
        <div className="audio-result">
          <div className="result-event">
            <AlertTriangle size={16} />
            <strong>{audioResult.sound_event}</strong>
          </div>
          <p>{audioResult.guidance}</p>
        </div>
      )}
      <div className="audio-actions" style={{ display: 'flex', gap: '1rem', width: '100%' }}>
        <button
          className={`btn-primary ${isLiveStreaming ? 'btn-danger' : ''}`}
          style={{ flex: 1 }}
          onClick={isLiveStreaming ? stopLiveStream : startLiveStream}
          disabled={isAnalyzing || isRecording}
        >
          {isLiveStreaming ? 'Stop Real-time' : 'Start Real-time Mode'}
        </button>
        <button
          className="btn-secondary"
          style={{ flex: 1 }}
          onClick={onListen}
          disabled={isAnalyzing || isRecording || isLiveStreaming}
        >
          {isAnalyzing ? 'Processing...' : 'Analyze Once'}
        </button>
      </div>
    </div>
  );

  const renderAudio = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Audio Guard</h2>
        <p className="text-muted-foreground">Continuous environmental sound detection.</p>
      </div>

      <Card className="border-primary/20">
        <CardContent className="flex flex-col items-center justify-center p-12 text-center">
          <AudioPane
            audioStatus={isRecording ? 'Listening...' : isAnalyzing ? 'Processing...' : 'Ready'}
            onListen={handleAudioListen}
            isAnalyzing={isAnalyzing}
            isRecording={isRecording}
            audioResult={audioResult}
            isLiveStreaming={isLiveStreaming}
            startLiveStream={startLiveStream}
            stopLiveStream={stopLiveStream}
          />
        </CardContent>
      </Card>

      {audioResult && (
        <Card className={audioResult.urgency === 'Critical' ? 'border-destructive bg-destructive/5' : ''}>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5" />
              Latest Detection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-medium mb-2">{audioResult.sound_event}</div>
            <p className="text-muted-foreground">{audioResult.guidance}</p>
            <Badge className="mt-4" variant={audioResult.urgency === 'Critical' ? 'destructive' : 'default'}>
              Urgency: {audioResult.urgency}
            </Badge>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your OmniSense preferences.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Accessibility Preferences</CardTitle>
          <CardDescription>Customize how OmniSense interacts with you.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Language Profile</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <option value="en">English (EN)</option>
              <option value="fr">French (FR)</option>
              <option value="hi">Hindi (HI)</option>
              <option value="or">Odia (OR)</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-0.5">
              <div className="text-base font-medium flex items-center">
                <Heart className="mr-2 h-4 w-4 text-primary" /> Senior Mode
              </div>
              <div className="text-sm text-muted-foreground">
                Enables wellness reminders and conversational companion features.
              </div>
            </div>
            <Button
              variant={seniorMode ? "default" : "outline"}
              onClick={() => setSeniorMode(!seniorMode)}
            >
              {seniorMode ? "Enabled" : "Disabled"}
            </Button>
          </div>
        </CardContent>
        <CardFooter className="bg-muted/30 p-6 flex justify-end">
          <Button variant="destructive" onClick={handleStopSystems}>
            Disconnect & Logout
          </Button>
        </CardFooter>
      </Card>
    </div>
  );

  return (
    <Layout currentView={currentView} setCurrentView={setCurrentView}>
      <AnimatePresence mode="wait">
        <motion.div
          key={currentView}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="h-full"
        >
          {currentView === 'dashboard' && renderDashboard()}
          {currentView === 'vision' && renderVision()}
          {currentView === 'audio' && renderAudio()}
          {currentView === 'settings' && renderSettings()}
        </motion.div>
      </AnimatePresence>

      {/* Global Alert Overlay */}
      <AnimatePresence>
        {activeAlert && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50 w-full max-w-md px-4 cursor-pointer"
            onClick={() => setActiveAlert(null)}
          >
            <Card className="border-destructive shadow-xl shadow-destructive/20">
              <CardContent className="p-6 flex items-start space-x-4 bg-destructive text-destructive-foreground rounded-lg">
                <AlertTriangle className="h-8 w-8 shrink-0" />
                <div>
                  <h4 className="text-lg font-bold">{activeAlert.title}</h4>
                  <p className="text-sm opacity-90">{activeAlert.message}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </Layout>
  );
};

export default App;
