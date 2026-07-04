import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { SEO } from "@/components/SEO";
import { motion } from "framer-motion";
import { Mic, MicOff, Loader2, Activity, Mail } from "lucide-react";
import logoMain from "@assets/logo-main.svg";

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error' | 'mic_error';
type ConversationState = 'idle' | 'listening' | 'processing' | 'speaking';

export default function VoiceAgent() {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [conversationState, setConversationState] = useState<ConversationState>('idle');
  const [transcript, setTranscript] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');
  const [isMicActive, setIsMicActive] = useState<boolean>(true);
  
  // Email input state
  const [email, setEmail] = useState<string>('');
  const [emailError, setEmailError] = useState<string>('');
  const [emailSubmitted, setEmailSubmitted] = useState<boolean>(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  
  // Media Recorder & Audio
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  
  // Playback Queue for gapless chunk playback
  const audioQueueRef = useRef<string[]>([]);
  const isProcessingQueueRef = useRef<boolean>(false);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const isResponseCompleteRef = useRef<boolean>(true);

  // VAD (Voice Activity Detection)
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const vadActiveRef = useRef<boolean>(false);
  const isSpeakingRef = useRef<boolean>(false);
  const hasSpokenRef = useRef<boolean>(false);
  const silenceStartRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Refs for values accessed inside requestAnimationFrame
  const stateRef = useRef<ConversationState>('idle');
  const isMicActiveRef = useRef<boolean>(true);

  useEffect(() => { stateRef.current = conversationState; }, [conversationState]);

  // ─── Email validation ──────────────────────────────────────────────
  const validateEmail = (value: string): boolean => {
    const re = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
    return re.test(value.trim());
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) {
      setEmailError('Please enter your email address.');
      return;
    }
    if (!validateEmail(trimmed)) {
      setEmailError('Please enter a valid email address.');
      return;
    }
    setEmailError('');
    setEmail(trimmed);
    setEmailSubmitted(true);
  };

  // ─── Audio Playback (Gapless) ──────────────────────────────────────
  const processAudioQueue = useCallback(async () => {
    if (isProcessingQueueRef.current) return;
    isProcessingQueueRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const base64Audio = audioQueueRef.current.shift()!;
      try {
        const audioStr = atob(base64Audio);
        const buffer = new ArrayBuffer(audioStr.length);
        const view = new Uint8Array(buffer);
        for (let i = 0; i < audioStr.length; i++) {
          view[i] = audioStr.charCodeAt(i);
        }

        if (!playbackContextRef.current) {
          playbackContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        if (playbackContextRef.current.state === 'suspended') {
          await playbackContextRef.current.resume();
        }

        const audioBuffer = await playbackContextRef.current.decodeAudioData(buffer);
        const source = playbackContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(playbackContextRef.current.destination);

        activeSourcesRef.current.push(source);

        const currentTime = playbackContextRef.current.currentTime;
        if (nextPlayTimeRef.current < currentTime + 0.05) {
          nextPlayTimeRef.current = currentTime + 0.05;
        }

        source.start(nextPlayTimeRef.current);
        nextPlayTimeRef.current += audioBuffer.duration;

        source.onended = () => {
          activeSourcesRef.current = activeSourcesRef.current.filter((s) => s !== source);
          
          // When all audio finished AND backend is done → restart listening
          if (activeSourcesRef.current.length === 0 && isResponseCompleteRef.current) {
            setConversationState('idle');
            startRecording();
          }
        };
      } catch (e) {
        console.error("Error decoding/playing audio", e);
      }
    }

    isProcessingQueueRef.current = false;
  }, []);

  const queueAudio = useCallback((base64Audio: string) => {
    audioQueueRef.current.push(base64Audio);
    processAudioQueue();
  }, [processAudioQueue]);

  // ─── VAD (Voice Activity Detection) ────────────────────────────────
  const checkAudioLevel = useCallback(() => {
    if (!vadActiveRef.current || !analyserRef.current) return;
    
    // If mic is toggled off, keep looping but don't detect anything
    if (!isMicActiveRef.current) {
      requestAnimationFrame(checkAudioLevel);
      return;
    }
    
    // Don't trigger VAD during processing or speaking
    if (stateRef.current === 'processing' || stateRef.current === 'speaking') {
      requestAnimationFrame(checkAudioLevel);
      return;
    }

    const analyser = analyserRef.current;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const average = sum / dataArray.length;

    const SILENCE_THRESHOLD = 25;
    const SILENCE_DURATION = 1500; // 1.5 seconds of silence = done speaking

    if (average > SILENCE_THRESHOLD) {
      if (!isSpeakingRef.current) {
        isSpeakingRef.current = true;
      }
      hasSpokenRef.current = true;
      silenceStartRef.current = null;
      if (stateRef.current === 'idle') {
        setConversationState('listening');
      }
    } else {
      if (isSpeakingRef.current) {
        if (silenceStartRef.current === null) {
          silenceStartRef.current = performance.now();
        } else if (performance.now() - silenceStartRef.current > SILENCE_DURATION) {
          isSpeakingRef.current = false;
          silenceStartRef.current = null;
          if (hasSpokenRef.current) {
            hasSpokenRef.current = false;
            stopAndSend();
          }
        }
      }
    }
    requestAnimationFrame(checkAudioLevel);
  }, []);

  // ─── Recording ─────────────────────────────────────────────────────
  const startRecording = () => {
    if (!streamRef.current) return;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') return;
    
    const mediaRecorder = new MediaRecorder(streamRef.current);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      if (audioChunksRef.current.length > 0) {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(audioBlob);
          setConversationState('processing');
        }
        audioChunksRef.current = [];
      }
    };

    mediaRecorder.start(250);
    setConversationState('idle');
  };

  const stopAndSend = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  // ─── Microphone Init ───────────────────────────────────────────────
  const initMicrophone = async () => {
    if (streamRef.current) return; // Already initialized
    
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);
    analyser.fftSize = 256;
    
    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    
    vadActiveRef.current = true;
    requestAnimationFrame(checkAudioLevel);
  };

  // ─── Mic Toggle (Pause / Resume) ──────────────────────────────────
  const toggleMic = () => {
    const newState = !isMicActiveRef.current;
    isMicActiveRef.current = newState;
    setIsMicActive(newState);

    if (!newState) {
      // User is pausing: stop current recording and send whatever was captured
      isSpeakingRef.current = false;
      hasSpokenRef.current = false;
      silenceStartRef.current = null;
      stopAndSend();
    } else {
      // User is resuming: start a fresh recording
      startRecording();
    }
  };

  // ─── Cleanup ───────────────────────────────────────────────────────
  const stopEverything = () => {
    vadActiveRef.current = false;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (playbackContextRef.current) {
      playbackContextRef.current.close();
      playbackContextRef.current = null;
    }
    activeSourcesRef.current.forEach(source => {
      try { source.stop(); } catch (e) {}
    });
    activeSourcesRef.current = [];
    nextPlayTimeRef.current = 0;
    audioQueueRef.current = [];
    isProcessingQueueRef.current = false;
  };

  // ─── WebSocket Connection ──────────────────────────────────────────
  const connectWebSocket = useCallback(async () => {
    setConnectionState('connecting');

    // 1. Initialize microphone first
    try {
      await initMicrophone();
    } catch (err) {
      console.error("Failed to initialize microphone:", err);
      setConnectionState('mic_error');
      return;
    }

    // 2. Connect WebSocket with email
    const ws = new WebSocket(`ws://127.0.0.1:8001/api/voice/stream?email=${encodeURIComponent(email)}`);

    ws.onopen = () => {
      setConnectionState('connected');
    };

    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "ready") {
            // Backend is ready — start listening for user's voice
            startRecording();
          } else if (data.type === "error") {
            console.error("Backend error:", data.message);
            setConnectionState('error');
          } else if (data.type === "no_speech") {
            // No speech detected, go back to listening
            setConversationState('idle');
            startRecording();
          } else if (data.type === "response_start") {
            setAiResponse('');
            isResponseCompleteRef.current = false;
            setConversationState('speaking');
          } else if (data.type === "response_chunk") {
            setAiResponse(prev => prev + " " + data.text);
          } else if (data.type === "response_complete") {
            setAiResponse(data.text);
            isResponseCompleteRef.current = true;
            if (activeSourcesRef.current.length === 0) {
              setConversationState('idle');
              startRecording();
            }
          } else if (data.type === "transcript") {
            setTranscript(data.text);
          } else if (data.type === "audio") {
            queueAudio(data.data);
          }
        } catch (err) {
          console.error("Failed to parse websocket message", err);
        }
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
      setConnectionState('error');
      stopEverything();
    };

    ws.onclose = () => {
      setConnectionState(prev => prev === 'error' ? 'error' : 'disconnected');
      setConversationState('idle');
      stopEverything();
    };

    wsRef.current = ws;
  }, [queueAudio, email]);

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setConnectionState('disconnected');
    setConversationState('idle');
    setAiResponse('');
    setTranscript('');
    setIsMicActive(true);
    isMicActiveRef.current = true;
    setEmailSubmitted(false);
    stopEverything();
  };

  const toggleConnection = () => {
    if (connectionState === 'disconnected' || connectionState === 'error') {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      stopEverything();
    };
  }, []);

  // ─── UI ────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <SEO
        title="AI Voice Agent | PP5 Media Solutions"
        description="Talk with our AI Consultant to learn about our services and schedule a meeting."
        canonical="/voice-agent"
      />
      <Navbar forceDarkText={true} customLogo={logoMain} />

      <main className="flex-grow pt-24 pb-16 md:pt-32">
        <div className="container mx-auto px-4 md:px-6 max-w-4xl">
          
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold font-display text-gray-900 mb-4">
              Talk with our AI Consultant
            </h1>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Experience the future of digital consulting. Our AI agent is here to understand your needs and guide you through our services.
            </p>

            {/* ─── Email Input (Step 1) ──────────────────────────── */}
            {connectionState === 'disconnected' && !emailSubmitted && (
              <motion.form 
                onSubmit={handleEmailSubmit}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-md mx-auto"
              >
                <div className="flex flex-col gap-3">
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        if (emailError) setEmailError('');
                      }}
                      placeholder="Enter your email to get started"
                      className="w-full pl-12 pr-4 py-4 rounded-2xl border-2 border-gray-200 bg-white text-gray-900 text-base font-medium focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-gray-400"
                      autoFocus
                    />
                  </div>
                  {emailError && (
                    <p className="text-red-500 text-sm font-medium">{emailError}</p>
                  )}
                  <button 
                    type="submit"
                    className="px-8 py-4 bg-primary text-white font-bold rounded-full hover:bg-green-600 transition-all shadow-lg hover:-translate-y-1"
                  >
                    Continue
                  </button>
                </div>
              </motion.form>
            )}

            {/* ─── Start Conversation (Step 2) ─────────────────── */}
            {connectionState === 'disconnected' && emailSubmitted && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-4"
              >
                <p className="text-sm text-gray-500">
                  Connecting as <span className="font-semibold text-gray-700">{email}</span>
                  <button 
                    onClick={() => setEmailSubmitted(false)} 
                    className="ml-2 text-primary hover:underline text-xs"
                  >
                    Change
                  </button>
                </p>
                <button 
                  onClick={toggleConnection}
                  className="px-8 py-4 bg-primary text-white font-bold rounded-full hover:bg-green-600 transition-all shadow-lg hover:-translate-y-1"
                >
                  Start Conversation
                </button>
              </motion.div>
            )}

            {connectionState === 'connecting' && (
              <button disabled className="px-8 py-4 bg-gray-400 text-white font-bold rounded-full flex items-center justify-center gap-2 mx-auto">
                <Loader2 className="w-5 h-5 animate-spin" /> Connecting...
              </button>
            )}
            {connectionState === 'error' && (
              <div className="text-red-500 font-bold mb-4">
                Failed to connect to the Voice Server (WebSocket error). Is the backend running?
                <br />
                <button onClick={toggleConnection} className="mt-4 px-6 py-2 bg-red-500 text-white rounded-full">Retry Connection</button>
              </div>
            )}
            {connectionState === 'mic_error' && (
              <div className="text-red-500 font-bold mb-4">
                Microphone Access Denied or Unavailable. Please grant permission in your browser!
                <br />
                <button onClick={toggleConnection} className="mt-4 px-6 py-2 bg-red-500 text-white rounded-full">Retry Connection</button>
              </div>
            )}
          </div>

          {connectionState === 'connected' && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100"
            >
              <div className="bg-gray-900 px-6 py-3 flex items-center justify-between text-white">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                  </span>
                  <span className="text-sm font-medium">Connected</span>
                  <span className="text-xs text-gray-400 ml-2">{email}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <Activity className="w-4 h-4" />
                  <span className="capitalize">{conversationState}</span>
                </div>
                <button 
                  onClick={disconnectWebSocket}
                  className="text-xs text-gray-400 hover:text-white transition-colors underline"
                >
                  Disconnect
                </button>
              </div>

              <div className="p-8 md:p-12 flex flex-col items-center">
                <div className="w-full mb-12">
                  <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 min-h-[120px] flex items-center justify-center">
                    <p className="text-lg text-gray-800 leading-relaxed font-medium">
                      {aiResponse || "Say something to start the conversation..."}
                    </p>
                  </div>
                </div>

                <div className="relative mb-12">
                  {conversationState === 'processing' && (
                    <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping scale-150" />
                  )}
                  {conversationState === 'listening' && isMicActive && (
                    <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping scale-125" />
                  )}
                  <motion.button
                    onClick={toggleMic}
                    animate={{ 
                      x: (isMicActive && conversationState === 'listening') ? -30 : 0,
                      scale: 1 
                    }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center text-white transition-colors shadow-xl cursor-pointer ${
                      !isMicActive
                        ? 'bg-gray-400 opacity-80'
                        : conversationState === 'listening' 
                        ? 'bg-red-500'
                        : conversationState === 'processing' || conversationState === 'speaking'
                        ? 'bg-yellow-500'
                        : 'bg-primary'
                    }`}
                  >
                    {!isMicActive ? (
                      <MicOff className="w-10 h-10" />
                    ) : conversationState === 'listening' ? (
                      <Mic className="w-10 h-10 animate-pulse" />
                    ) : conversationState === 'processing' ? (
                      <Loader2 className="w-10 h-10 animate-spin" />
                    ) : (
                      <Mic className="w-10 h-10" />
                    )}
                  </motion.button>
                  <p className="text-center text-xs text-gray-400 mt-4">
                    {!isMicActive 
                      ? "Mic paused — click to resume"
                      : conversationState === 'idle' ? "Speak to begin..." :
                        conversationState === 'listening' ? "Listening (auto-detects when you stop)" :
                        conversationState === 'processing' ? "Thinking..." : "Speaking..."}
                  </p>
                </div>

                <div className="w-full">
                  <p className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2 text-center">Live Transcript</p>
                  <div className="bg-gray-50 rounded-xl p-4 min-h-[80px] text-gray-600 text-center italic border border-gray-100 flex items-center justify-center">
                    {transcript || "Waiting for you to speak..."}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

        </div>
      </main>

      <Footer />
    </div>
  );
}
