/**
 * FilesTab — event file management (upload, view, delete reference files).
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload, Trash2, FileImage, FileSpreadsheet, FileText, Eye, Download
} from 'lucide-react';
import { apiClient } from '../../lib/api';

interface EventFile {
  id: string;
  filename: string;
  type: string;
  content_type: string;
  size: number;
  uploaded_at: string;
}

interface FilesTabProps {
  eventId: string;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getIcon(type: string) {
  if (type === 'image') return <FileImage size={20} className="text-blue-500" />;
  if (type === 'excel') return <FileSpreadsheet size={20} className="text-green-500" />;
  if (type === 'pdf') return <FileText size={20} className="text-red-500" />;
  return <FileText size={20} className="text-gray-500" />;
}

export function FilesTab({ eventId }: FilesTabProps) {
  const queryClient = useQueryClient();
  const [dragOver, setDragOver] = useState(false);

  const { data: files = [], isLoading } = useQuery({
    queryKey: ['event-files', eventId],
    queryFn: () => apiClient.listEventFiles(eventId) as Promise<EventFile[]>,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadEventFile(eventId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['event-files', eventId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => apiClient.deleteEventFile(eventId, fileId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['event-files', eventId] }),
  });

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    Array.from(fileList).forEach((f) => uploadMutation.mutate(f));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="space-y-4">
      {/* Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragOver ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400'
        }`}
      >
        <label className="cursor-pointer">
          <input type="file" multiple accept="image/*,.xlsx,.xls,.csv,.pdf,.doc,.docx,.pptx"
            onChange={(e) => handleFiles(e.target.files)} className="hidden" />
          <Upload className="mx-auto mb-3 text-gray-400" size={36} />
          <p className="text-sm font-medium text-gray-700 mb-1">
            拖拽文件到这里，或点击上传
          </p>
          <p className="text-xs text-gray-500">
            支持图片、Excel、PDF、Word、PPT（最大 20MB）
          </p>
        </label>
        {uploadMutation.isPending && (
          <p className="text-xs text-indigo-600 mt-2">上传中...</p>
        )}
      </div>

      {/* File List */}
      {isLoading ? (
        <div className="text-center text-gray-500 py-8">加载中...</div>
      ) : (files as EventFile[]).length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <FileText size={48} className="mx-auto mb-3 text-gray-300" />
          <p className="text-sm">还没有文件</p>
          <p className="text-xs text-gray-400 mt-1">
            上传邀请函、会场图、参会名单等参考文件，AI 助手可以读取分析
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(files as EventFile[]).map((file) => (
            <div key={file.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow group">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getIcon(file.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate" title={file.filename}>
                    {file.filename}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatSize(file.size)} · {new Date(file.uploaded_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                {(file.type === 'image' || file.type === 'pdf') && (
                  <a href={apiClient.getEventFileUrl(eventId, file.id)} target="_blank" rel="noreferrer"
                    className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-xs text-indigo-600 bg-indigo-50 rounded hover:bg-indigo-100 transition-colors">
                    <Eye size={12} /> 预览
                  </a>
                )}
                <a href={`${apiClient.getEventFileUrl(eventId, file.id)}?download=1`} download
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-xs text-gray-600 bg-gray-50 rounded hover:bg-gray-100 transition-colors">
                  <Download size={12} /> 下载
                </a>
                <button
                  onClick={() => { if (confirm(`删除 ${file.filename}？`)) deleteMutation.mutate(file.id); }}
                  className="flex items-center justify-center gap-1 px-2 py-1 text-xs text-red-600 bg-red-50 rounded hover:bg-red-100 transition-colors">
                  <Trash2 size={12} /> 删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
