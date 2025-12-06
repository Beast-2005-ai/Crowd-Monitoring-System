import React, { useState, useEffect, useRef } from 'react';
import { Monitor, Wifi, WifiOff, Video, Settings, Terminal } from 'lucide-react';

// --- Main Application Component ---
function App() {
  const [ipAddress, setIpAddress]       = useState('');
  const [isConnected, setIsConnected]   = useState(false);
  const [streamUrl, setStreamUrl]       = useState('');
  const [isLoading, setIsLoading]       = useState(false);
  const [streamError, setStreamError]   = useState(false);
  const [logMessages, setLogMessages]   = useState<string[]>([]);
  const terminalRef                     = useRef<HTMLDivElement>(null);

  // --- MODIFIED: More Realistic and State-Aware Terminal ---
  useEffect(() => {
    let logTimer: NodeJS.Timeout;

    // Clear previous logs whenever the connection state changes
    setLogMessages([]);

    if (isLoading) {
      setLogMessages([`[INFO] Attempting connection to ${ipAddress}...`]);
    } else if (streamError) {
      setLogMessages([`[ERROR] Connection failed. Please check the IP address, network connection, and ensure the server is running on the Raspberry Pi.`]);
    } else if (isConnected) {
      setLogMessages([`[SUCCESS] Connection established. Starting video stream...`]);

      // This function generates a variety of realistic-looking logs
      const generateLog = () => {
        const realisticLogs = [
          "0: 640x480 {D} Humans, {T}ms",
          "Speed: {P}ms preprocess, {T}ms inference, {PO}ms postprocess",
          "[DEBUG] Frame received from stream source.",
          "[INFO] Tracker updated with {D} objects.",
          "[WARN] Low confidence detection ignored.",
          "0: 640x480 {D} Humans, {T}ms",
        ];
        
        const template = realisticLogs[Math.floor(Math.random() * realisticLogs.length)];
        const detections = Math.floor(Math.random() * 6);
        const time = (Math.random() * (700 - 450) + 450).toFixed(1);
        const pre = (Math.random() * 25).toFixed(1);
        const post = (Math.random() * 15).toFixed(1);
        
        const newMessage = template
          .replace('{D}', detections.toString())
          .replace('{T}', time)
          .replace('{P}', pre)
          .replace('{PO}', post);

        setLogMessages(prev => [...prev.slice(-15), newMessage]); // Keep the log from getting too long
        
        const nextInterval = Math.random() * (3000 - 900) + 900; // More natural, varied timing
        logTimer = setTimeout(generateLog, nextInterval);
      };
      
      // Start the log generation after a short delay to feel more real
      logTimer = setTimeout(generateLog, 2000);
    }
    
    // Cleanup function to stop the timer when the component unmounts or state changes
    return () => clearTimeout(logTimer);
  }, [isConnected, isLoading, streamError, ipAddress]);


  // Effect to auto-scroll the terminal to the bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logMessages]);

  const handleConnect = async () => {
    if (!isValidIP(ipAddress)) return;
    setIsLoading(true);
    setStreamError(false);
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate connection time
    const url = `http://${ipAddress.trim()}:5123/video_feed`;
    setStreamUrl(url);
    setIsConnected(true);
    setIsLoading(false);
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    setStreamUrl('');
    setStreamError(false);
    setIsLoading(false);
  };
  
  const handleImageError = () => {
      setIsLoading(false); // Stop loading if image fails
      setStreamError(true);
  };
  const handleImageLoad = () => {
      setIsLoading(false); // Stop loading on success
      setStreamError(false);
  };
  
  const isValidIP = (ip: string) => /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip.trim());

  // Helper component to apply colors to log messages
  const LogLine = ({ text }: { text: string }) => {
    let colorClass = "text-green-400"; // Default matrix green
    if (text.startsWith('[ERROR]')) colorClass = "text-red-400";
    if (text.startsWith('[WARN]')) colorClass = "text-yellow-400";
    if (text.startsWith('[INFO]') || text.startsWith('[SUCCESS]')) colorClass = "text-blue-400";

    return <p className={`whitespace-pre-wrap ${colorClass}`}>&gt; {text}</p>;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center space-x-3">
          <div className="p-2 bg-blue-600 rounded-lg"><Monitor className="h-6 w-6" /></div>
          <div>
            <h1 className="text-xl font-bold text-white">Crowd Monitoring Dashboard</h1>
            <p className="text-sm text-gray-400">Real-time YOLOv8 stream from Raspberry Pi</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!isConnected ? (
          <div className="max-w-md mx-auto">
            <div className="bg-gray-800 rounded-xl p-8 shadow-2xl border border-gray-700">
              <div className="text-center mb-8">
                <div className="inline-flex p-3 bg-gray-700 rounded-full mb-4">
                  <Settings className="h-8 w-8 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Connect to Stream</h2>
                <p className="text-gray-400">Enter your Raspberry Pi's IP address to begin monitoring</p>
              </div>
              <div className="space-y-6">
                <div>
                  <label htmlFor="ip-address" className="block text-sm font-medium text-gray-300 mb-2">IP Address</label>
                  <input
                    id="ip-address"
                    type="text"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    placeholder="192.168.1.55"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    disabled={isLoading}
                  />
                  {ipAddress && !isValidIP(ipAddress) && (
                    <p className="mt-2 text-sm text-red-400">Please enter a valid IP address</p>
                  )}
                </div>
                <button
                  onClick={handleConnect}
                  disabled={!ipAddress.trim() || !isValidIP(ipAddress) || isLoading}
                  className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-all transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Connecting...</span>
                    </>
                  ) : (
                    <>
                      <Wifi className="h-4 w-4" />
                      <span>Connect</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="flex flex-col lg:flex-row gap-8">
              <div className="flex-[3] bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-700">
                <div className="flex items-center space-x-2 mb-4">
                  <Video className="h-5 w-5 text-blue-400" />
                  <h3 className="text-lg font-semibold">Live Video Feed</h3>
                </div>
                <div className="relative bg-black rounded-lg overflow-hidden shadow-inner aspect-video">
                  {(isLoading || !streamError) && (
                    <img id="video-stream" src={streamUrl} alt="Live video stream" onError={handleImageError} onLoad={handleImageLoad} className="w-full h-full object-contain" />
                  )}
                  {streamError && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4">
                      <WifiOff className="h-12 w-12 text-red-400 mb-4" />
                      <p className="font-semibold text-red-400">Connection Error</p>
                      <p className="text-sm text-gray-400 mt-1">Unable to load stream from {ipAddress}</p>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex-[1] bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-700">
                  <h3 className="text-lg font-semibold mb-4 text-blue-400">System Status</h3>
                  <div className="space-y-3 text-sm">
                      <p><strong>Status:</strong> <span className={streamError ? "text-red-400" : "text-green-400"}>{streamError ? "Error" : "Connected"}</span></p>
                      <p><strong>Source IP:</strong> <span className="text-gray-300">{ipAddress}</span></p>
                      <p><strong>Model:</strong> <span className="text-gray-300">best.onnx</span></p>
                      <p className="text-gray-400 pt-2 border-t border-gray-700 mt-4">This feed displays live person detection from the YOLOv8 model on the Raspberry Pi.</p>
                  </div>
              </div>
            </div>
            <div className="bg-gray-800 rounded-xl shadow-2xl border border-gray-700">
              <div className="flex items-center space-x-2 p-3 bg-gray-900/50 rounded-t-xl border-b border-gray-700">
                <Terminal className="h-5 w-5 text-gray-400" />
                <h3 className="text-md font-semibold text-gray-300">Backend Logs (Live Simulation)</h3>
              </div>
              <div ref={terminalRef} className="p-4 h-48 overflow-y-auto bg-black font-mono text-sm scroll-smooth">
                {logMessages.map((msg, index) => (
                  <LogLine key={index} text={msg} />
                ))}
              </div>
            </div>
            <div className="text-center pt-4">
                <button onClick={handleDisconnect} className="flex items-center justify-center space-x-2 mx-auto px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-all">
                    <WifiOff className="h-4 w-4" />
                    <span>Disconnect</span>
                </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;