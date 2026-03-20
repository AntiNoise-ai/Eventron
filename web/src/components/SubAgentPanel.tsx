/**
 * SubAgentPanel — Reusable scoped AI assistant panel for each tab.
 *
 * Each tab (attendees, badges, checkin, etc.) gets its own sub-agent with:
 * - Scoped conversation (different session per scope)
 * - File upload support
 * - Task plan display
 * - Collapsible sidebar layout
 */
import { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bot, Send, Paperclip, X, ChevronRight, ChevronLeft,
  FileImage, FileSpreadsheet, FileText, Loader2
} from 'lucide-react';
import { apiClient } from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  attachments?: { name: string; type: string }[];
}

interface SubAgentPanelProps {
  eventId: string;
  scope: string;         // e.g. "organizer", "badge", "checkin"
  title: string;         // e.g. "铭牌设计助手"
  placeholder?: string;  // input placeholder
  welcomeMessage: string;
}

export function SubAgentPanel({
  eventId,
  scope,
  title,
  placeholder = '描述你的需求...',
  welcomeMessage,
}: SubAgentPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: welcomeMessage },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: ({ msg, files }: { msg: string; files: File[] }) =>
      apiClient.sendAgentChat(msg, {
        eventId,
        sessionId: sessionId || undefined,
        scope,
        files,
      }),
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply },
      ]);
      if (data.action_taken) {
        queryClient.invalidateQueries();
      }
    },
    onError: (err) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `出错了：${err instanceof Error ? err.message : '请重试'}` },
      ]);
    },
  });

  const handleSend = () => {
    const msg = input.trim();
    const files = [...pendingFiles];
    if ((!msg && files.length === 0) || chatMutation.isPending) return;

    const attachments = files.map((f) => ({
      name: f.name,
      type: f.type.startsWith('image/') ? 'image' : f.name.endsWith('.xlsx') ? 'excel' : 'file',
    }));

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: msg || `上传了 ${files.length} 个文件`,
        attachments: attachments.length > 0 ? attachments : undefined,
      },
    ]);
    setInput('');
    setPendingFiles([]);
    chatMutation.mutate({ msg: msg || '请分析这些文件', files });
  };

  if (isCollapsed) {
    return (
      <div
        onClick={() => setIsCollapsed(false)}
        className="w-10 bg-indigo-50 border-l border-gray-200 flex flex-col items-center justify-center cursor-pointer hover:bg-indigo-100 transition-colors"
      >
        <ChevronLeft size={16} className="text-indigo-600 mb-2" />
        <div className="writing-mode-vertical text-xs text-indigo-600 font-medium" style={{ writingMode: 'vertical-rl' }}>
          {title}
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 border-l border-gray-200 bg-white flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-200 flex items-center justify-between bg-indigo-50">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-indigo-600" />
          <span className="text-sm font-semibold text-indigo-700">{title}</span>
        </div>
        <button onClick={() => setIsCollapsed(true)} className="p-1 hover:bg-indigo-100 rounded">
          <ChevronRight size={14} className="text-indigo-600" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'text-right' : ''}`}>
              {msg.attachments && (
                <div className={`flex flex-wrap gap-1 mb-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.attachments.map((att, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[10px]">
                      {att.type === 'image' ? <FileImage size={8} /> : <FileText size={8} />}
                      {att.name.length > 15 ? att.name.slice(0, 12) + '...' : att.name}
                    </span>
                  ))}
                </div>
              )}
              <div className={`px-2.5 py-1.5 rounded-lg text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {msg.content.split('\n').map((line, i) => (
                  <span key={i}>{line}{i < msg.content.split('\n').length - 1 && <br />}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="flex gap-2">
            <div className="bg-gray-100 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5">
              <Loader2 size={12} className="animate-spin text-indigo-600" />
              <span className="text-[10px] text-gray-500">思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div className="px-3 py-1 border-t border-gray-100 flex flex-wrap gap-1">
          {pendingFiles.map((f, i) => (
            <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-100 rounded text-[10px]">
              {f.name.length > 12 ? f.name.slice(0, 10) + '...' : f.name}
              <button onClick={() => setPendingFiles((p) => p.filter((_, j) => j !== i))} className="text-gray-400 hover:text-red-500">
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-2">
        <div className="flex gap-1.5 items-end">
          <input ref={fileInputRef} type="file" multiple accept="image/*,.xlsx,.xls,.csv,.pdf" onChange={(e) => {
            setPendingFiles((p) => [...p, ...Array.from(e.target.files || [])]);
            e.target.value = '';
          }} className="hidden" />
          <button onClick={() => fileInputRef.current?.click()} disabled={chatMutation.isPending}
            className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors disabled:opacity-50">
            <Paperclip size={14} />
          </button>
          <input
            type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder={placeholder} disabled={chatMutation.isPending}
            className="flex-1 px-2 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button onClick={handleSend} disabled={(!input.trim() && !pendingFiles.length) || chatMutation.isPending}
            className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
