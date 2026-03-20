import { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MessageCircle, Send, X, Minimize2, Bot, User,
  Paperclip, FileImage, FileSpreadsheet, FileText, Loader2
} from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: { name: string; type: string }[];
}

interface SubTask {
  id: string;
  plugin: string;
  description: string;
  status: string;
}

interface ChatResponse {
  reply: string;
  session_id: string;
  event_id: string | null;
  action_taken: string | null;
  task_plan: SubTask[] | null;
}

interface AgentChatProps {
  eventId?: string;
}

export function AgentChat({ eventId }: AgentChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        '你好！我是 Eventron 智能排座助手。\n\n' +
        '你可以：\n' +
        '· 上传邀请函图片 → 自动提取活动信息\n' +
        '· 上传 Excel 名单 → 自动导入参会者\n' +
        '· 描述需求 → 自动规划会场+铭牌+签到\n' +
        '· 说「创建活动」→ 对话式引导创建\n\n' +
        '试试上传一张活动海报开始吧！',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [taskPlan, setTaskPlan] = useState<SubTask[] | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);
  useEffect(() => {
    if (isOpen && !isMinimized) inputRef.current?.focus();
  }, [isOpen, isMinimized]);

  const chatMutation = useMutation({
    mutationFn: async ({ message, files }: { message: string; files: File[] }) => {
      const formData = new FormData();
      formData.append('message', message);
      if (eventId) formData.append('event_id', eventId);
      if (sessionId) formData.append('session_id', sessionId);
      files.forEach((f) => formData.append('files', f));

      const token = localStorage.getItem('token');
      const resp = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || resp.statusText);
      }
      return resp.json() as Promise<ChatResponse>;
    },
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply, timestamp: new Date() },
      ]);
      if (data.task_plan) setTaskPlan(data.task_plan);
      if (data.action_taken) {
        queryClient.invalidateQueries({ queryKey: ['seats'] });
        queryClient.invalidateQueries({ queryKey: ['attendees'] });
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['event'] });
      }
    },
    onError: (err) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `出错了：${err instanceof Error ? err.message : '请重试'}`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = () => {
    const msg = input.trim();
    const files = [...pendingFiles];
    if ((!msg && files.length === 0) || chatMutation.isPending) return;

    const attachments = files.map((f) => ({
      name: f.name,
      type: f.type.startsWith('image/') ? 'image' :
            f.name.endsWith('.xlsx') || f.name.endsWith('.csv') ? 'excel' :
            f.name.endsWith('.pdf') ? 'pdf' : 'file',
    }));

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: msg || `上传了 ${files.length} 个文件`,
        timestamp: new Date(),
        attachments: attachments.length > 0 ? attachments : undefined,
      },
    ]);
    setInput('');
    setPendingFiles([]);
    chatMutation.mutate({ message: msg || '请分析这些文件', files });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setPendingFiles((prev) => [...prev, ...files]);
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <FileImage size={14} />;
    if (file.name.match(/\.(xlsx?|csv)$/i)) return <FileSpreadsheet size={14} />;
    if (file.name.endsWith('.pdf')) return <FileText size={14} />;
    return <FileText size={14} />;
  };

  // Floating button
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all hover:scale-105 flex items-center justify-center z-50"
        title="AI 排座助手"
      >
        <MessageCircle size={24} />
      </button>
    );
  }

  // Minimized
  if (isMinimized) {
    return (
      <div
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 right-6 bg-indigo-600 text-white rounded-full px-4 py-2 shadow-lg cursor-pointer hover:bg-indigo-700 transition-all flex items-center gap-2 z-50"
      >
        <Bot size={18} />
        <span className="text-sm font-medium">AI 助手</span>
        {chatMutation.isPending && (
          <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
        )}
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-[420px] h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 border border-gray-200">
      {/* Header */}
      <div className="bg-indigo-600 text-white px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Bot size={20} />
          <div>
            <span className="font-semibold text-sm">Eventron AI 助手</span>
            <span className="text-xs text-indigo-200 ml-2">多模态 · 多Agent</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setIsMinimized(true)} className="p-1 hover:bg-indigo-500 rounded transition-colors">
            <Minimize2 size={16} />
          </button>
          <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-indigo-500 rounded transition-colors">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Task Plan Banner */}
      {taskPlan && taskPlan.length > 0 && (
        <div className="bg-indigo-50 border-b border-indigo-100 px-4 py-2 flex-shrink-0">
          <div className="text-xs font-semibold text-indigo-700 mb-1">📋 任务计划</div>
          <div className="space-y-1">
            {taskPlan.map((task) => (
              <div key={task.id} className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${
                  task.status === 'done' ? 'bg-green-500' :
                  task.status === 'in_progress' ? 'bg-yellow-500 animate-pulse' :
                  task.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                }`} />
                <span className="text-gray-600">[{task.plugin}]</span>
                <span className="text-gray-800 truncate">{task.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-green-100 text-green-600'
            }`}>
              {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className="max-w-[80%]">
              {/* Attachment badges */}
              {msg.attachments && (
                <div className={`flex flex-wrap gap-1 mb-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.attachments.map((att, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs">
                      {att.type === 'image' ? <FileImage size={10} /> :
                       att.type === 'excel' ? <FileSpreadsheet size={10} /> :
                       <FileText size={10} />}
                      {att.name}
                    </span>
                  ))}
                </div>
              )}
              <div className={`px-3 py-2 rounded-xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-sm'
                  : 'bg-gray-100 text-gray-800 rounded-tl-sm'
              }`}>
                {msg.content.split('\n').map((line, i) => (
                  <span key={i}>
                    {line}
                    {i < msg.content.split('\n').length - 1 && <br />}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0">
              <Bot size={14} />
            </div>
            <div className="bg-gray-100 px-3 py-2 rounded-xl rounded-tl-sm flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-indigo-600" />
              <span className="text-xs text-gray-500">Agent 思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Pending files preview */}
      {pendingFiles.length > 0 && (
        <div className="border-t border-gray-100 px-3 py-2 flex-shrink-0">
          <div className="flex flex-wrap gap-1">
            {pendingFiles.map((file, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded-lg text-xs text-gray-700">
                {getFileIcon(file)}
                <span className="max-w-[120px] truncate">{file.name}</span>
                <button
                  onClick={() => removeFile(idx)}
                  className="ml-1 text-gray-400 hover:text-red-500"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-3 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,.xlsx,.xls,.csv,.pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={chatMutation.isPending}
            className="p-2 text-gray-400 hover:text-indigo-600 transition-colors disabled:opacity-50"
            title="上传文件（图片/Excel/PDF）"
          >
            <Paperclip size={18} />
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述需求或上传文件..."
            disabled={chatMutation.isPending}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={(!input.trim() && pendingFiles.length === 0) || chatMutation.isPending}
            className="px-3 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
