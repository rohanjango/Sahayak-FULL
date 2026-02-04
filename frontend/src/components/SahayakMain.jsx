import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Send, Brain, Eye, Zap, History, Settings, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';

const SahayakMain = ({ api }) => {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [executionLog, setExecutionLog] = useState([]);
  const [screenshots, setScreenshots] = useState([]);
  const [history, setHistory] = useState([]);
  const [mode, setMode] = useState('guided');
  const [userId, setUserId] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate or retrieve user ID
    const storedUserId = localStorage.getItem('sahayak_user_id');
    if (storedUserId) {
      setUserId(storedUserId);
    } else {
      const newUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('sahayak_user_id', newUserId);
      setUserId(newUserId);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [executionLog]);

  const handleExecute = async () => {
    if (!command.trim()) {
      toast.error('Please enter a command');
      return;
    }

    setLoading(true);
    setExecutionLog([]);
    setScreenshots([]);

    try {
      const response = await axios.post(`${api}/execute`, {
        user_id: userId,
        command: command,
        mode: mode
      });

      if (response.data.success) {
        toast.success('Command executed successfully!');
        setExecutionLog(response.data.execution_log || []);
        setScreenshots(response.data.screenshots || []);
        
        // Add to history
        setHistory(prev => [{
          command,
          timestamp: new Date().toISOString(),
          success: true
        }, ...prev].slice(0, 10));
      } else {
        toast.error(response.data.message || 'Execution failed');
        setExecutionLog([{ error: response.data.message }]);
      }
    } catch (error) {
      console.error('Execution error:', error);
      toast.error(error.response?.data?.detail || 'Failed to execute command');
      setExecutionLog([{ error: error.message }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleExecute();
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-[#0f0f10]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold" data-testid="app-title">Sahayak</h1>
              <p className="text-xs text-zinc-400">Autonomous Browser Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge 
              variant="outline" 
              className="border-zinc-700 text-zinc-300"
              data-testid="mode-badge"
            >
              Mode: {mode === 'guided' ? 'Guided' : 'Autonomous'}
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Command Input */}
          <div className="lg:col-span-2 space-y-6">
            {/* Command Input Card */}
            <Card 
              className="bg-zinc-900/50 border-zinc-800 backdrop-blur-sm p-6" 
              data-testid="command-input-card"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-400" />
                  <h2 className="text-lg font-semibold">Enter Your Command</h2>
                </div>
                
                <Textarea
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Example: Go to google.com and search for 'AI news'"
                  className="min-h-[120px] bg-zinc-950/50 border-zinc-700 focus:border-blue-500 text-white placeholder:text-zinc-500 resize-none"
                  data-testid="command-textarea"
                />
                
                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <Button
                      variant={mode === 'guided' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setMode('guided')}
                      className={mode === 'guided' ? 'bg-blue-600 hover:bg-blue-700' : 'border-zinc-700 hover:bg-zinc-800'}
                      data-testid="guided-mode-btn"
                    >
                      Guided
                    </Button>
                    <Button
                      variant={mode === 'autonomous' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setMode('autonomous')}
                      className={mode === 'autonomous' ? 'bg-cyan-600 hover:bg-cyan-700' : 'border-zinc-700 hover:bg-zinc-800'}
                      data-testid="autonomous-mode-btn"
                    >
                      <Zap className="w-4 h-4 mr-1" />
                      Autonomous
                    </Button>
                  </div>
                  
                  <Button
                    onClick={handleExecute}
                    disabled={loading || !command.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    data-testid="execute-btn"
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Execute
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>

            {/* Execution Log */}
            <Card 
              className="bg-zinc-900/50 border-zinc-800 backdrop-blur-sm p-6" 
              data-testid="execution-log-card"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-lg font-semibold">Execution Log</h2>
                </div>
                
                <ScrollArea className="h-[400px] w-full rounded-lg bg-zinc-950/50 border border-zinc-800 p-4">
                  {executionLog.length === 0 && !loading ? (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500" data-testid="empty-log">
                      <Brain className="w-12 h-12 mb-3 opacity-20" />
                      <p className="text-sm">No execution log yet</p>
                      <p className="text-xs mt-1">Enter a command to get started</p>
                    </div>
                  ) : (
                    <div className="space-y-3" data-testid="log-entries">
                      {executionLog.map((log, idx) => (
                        <div 
                          key={idx} 
                          className="p-3 bg-zinc-900/50 rounded-lg border border-zinc-800 animate-fade-in"
                          data-testid={`log-entry-${idx}`}
                        >
                          <div className="flex items-start gap-3">
                            <Badge 
                              variant="outline" 
                              className="mt-1 border-zinc-700 text-xs"
                            >
                              #{log.step}
                            </Badge>
                            <div className="flex-1">
                              {log.action && (
                                <div className="text-sm">
                                  <span className="text-blue-400 font-mono">{log.action.action}</span>
                                  {log.action.target && (
                                    <span className="text-zinc-400 ml-2">→ {log.action.target}</span>
                                  )}
                                </div>
                              )}
                              {log.result && (
                                <div className="text-xs text-zinc-500 mt-1">
                                  {JSON.stringify(log.result, null, 2)}
                                </div>
                              )}
                              {log.analysis && (
                                <div className="text-xs text-cyan-400 mt-2">
                                  Analysis: {log.analysis.analysis?.description || 'Processing...'}
                                </div>
                              )}
                              {log.error && (
                                <div className="text-xs text-red-400 mt-1">
                                  Error: {log.error}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                  
                  {loading && executionLog.length === 0 && (
                    <div className="flex items-center justify-center h-full" data-testid="loading-indicator">
                      <div className="text-center">
                        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                        <p className="text-sm text-zinc-400">AI is thinking...</p>
                      </div>
                    </div>
                  )}
                </ScrollArea>
              </div>
            </Card>
          </div>

          {/* Right Column - Screenshots & History */}
          <div className="space-y-6">
            {/* Screenshots */}
            <Card 
              className="bg-zinc-900/50 border-zinc-800 backdrop-blur-sm p-6" 
              data-testid="screenshots-card"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-purple-400" />
                  <h2 className="text-lg font-semibold">Screenshots</h2>
                </div>
                
                <ScrollArea className="h-[300px] w-full">
                  {screenshots.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500" data-testid="no-screenshots">
                      <Eye className="w-10 h-10 mb-2 opacity-20" />
                      <p className="text-sm">No screenshots yet</p>
                    </div>
                  ) : (
                    <div className="space-y-3" data-testid="screenshot-list">
                      {screenshots.map((screenshot, idx) => (
                        <div 
                          key={idx} 
                          className="rounded-lg border border-zinc-800 overflow-hidden animate-fade-in"
                          data-testid={`screenshot-${idx}`}
                        >
                          <img 
                            src={`data:image/png;base64,${screenshot}`} 
                            alt={`Screenshot ${idx + 1}`}
                            className="w-full h-auto"
                          />
                          <div className="p-2 bg-zinc-950/50">
                            <p className="text-xs text-zinc-400">Screenshot #{idx + 1}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </Card>

            {/* History */}
            <Card 
              className="bg-zinc-900/50 border-zinc-800 backdrop-blur-sm p-6" 
              data-testid="history-card"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <History className="w-5 h-5 text-green-400" />
                  <h2 className="text-lg font-semibold">Recent History</h2>
                </div>
                
                <ScrollArea className="h-[200px] w-full">
                  {history.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500" data-testid="no-history">
                      <History className="w-10 h-10 mb-2 opacity-20" />
                      <p className="text-sm">No history yet</p>
                    </div>
                  ) : (
                    <div className="space-y-2" data-testid="history-list">
                      {history.map((item, idx) => (
                        <div 
                          key={idx} 
                          className="p-3 bg-zinc-950/50 rounded-lg border border-zinc-800 cursor-pointer hover:border-zinc-700 transition-colors"
                          onClick={() => setCommand(item.command)}
                          data-testid={`history-item-${idx}`}
                        >
                          <p className="text-sm text-zinc-300 line-clamp-2">{item.command}</p>
                          <p className="text-xs text-zinc-500 mt-1">
                            {new Date(item.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </Card>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { icon: Brain, title: 'AI Planning', desc: 'Smart command interpretation', color: 'blue' },
            { icon: Eye, title: 'Vision AI', desc: 'Screenshot understanding', color: 'purple' },
            { icon: Zap, title: 'Self-Healing', desc: 'Adaptive selectors', color: 'yellow' },
            { icon: Settings, title: 'Memory', desc: 'Saves preferences', color: 'green' },
            { icon: Sparkles, title: 'Autonomous', desc: 'Goal-driven execution', color: 'cyan' },
          ].map((feature, idx) => (
            <Card 
              key={idx} 
              className="bg-zinc-900/30 border-zinc-800 p-4 hover:border-zinc-700 transition-colors"
              data-testid={`feature-${idx}`}
            >
              <feature.icon className={`w-8 h-8 text-${feature.color}-400 mb-2`} />
              <h3 className="font-semibold text-sm mb-1">{feature.title}</h3>
              <p className="text-xs text-zinc-400">{feature.desc}</p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SahayakMain;