import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Download, AlertCircle } from 'lucide-react';
import { apiClient } from '../../lib/api';

interface ImportTabProps {
  eventId: string;
}

interface PreviewData {
  detected_columns: Record<string, string>;
  preview_rows: any[];
  duplicates: any[];
}

export function ImportTab({ eventId }: ImportTabProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const previewMutation = useMutation({
    mutationFn: async (file: File) => {
      return apiClient.previewImport(eventId, file);
    },
    onSuccess: (data) => {
      setPreviewData(data as any);
      setColumnMapping((data as any).detected_columns || {});
      setError('');
    },
    onError: (err) => {
      setError(
        err instanceof Error ? err.message : '预览失败，请检查文件格式'
      );
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!previewData) throw new Error('No preview data');
      return apiClient.confirmImport(eventId, {
        column_mapping: columnMapping,
        attendees_data: previewData.preview_rows,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendees'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setSelectedFile(null);
      setPreviewData(null);
      setColumnMapping({});
      setError('');
      alert('导入成功！');
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '导入失败');
    },
  });

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setError('');
    previewMutation.mutate(file);
  };

  const handleColumnMappingChange = (column: string, value: string) => {
    setColumnMapping({
      ...columnMapping,
      [column]: value,
    });
  };

  const handleConfirmImport = () => {
    if (confirm('确定要导入这些参会人吗？')) {
      confirmMutation.mutate();
    }
  };

  if (previewData) {
    return (
      <div className="space-y-4">
        {/* Warning */}
        {previewData.duplicates && previewData.duplicates.length > 0 && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex gap-3">
            <AlertCircle className="text-yellow-600 flex-shrink-0" size={20} />
            <div>
              <p className="font-medium text-yellow-900">检测到重复数据</p>
              <p className="text-sm text-yellow-700">
                发现 {previewData.duplicates.length} 条可能的重复记录
              </p>
            </div>
          </div>
        )}

        {/* Column Mapping */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">列映射设置</h3>
          <div className="space-y-4">
            {Object.entries(previewData.detected_columns).map(([fileCol, mappedCol]) => (
              <div key={fileCol} className="grid grid-cols-3 gap-4 items-center">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    文件列: {fileCol}
                  </label>
                </div>
                <div className="text-center text-gray-500">→</div>
                <div>
                  <input
                    type="text"
                    value={columnMapping[fileCol] || mappedCol}
                    onChange={(e) =>
                      handleColumnMappingChange(fileCol, e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="输入映射的列名"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Preview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            预览数据 ({previewData.preview_rows.length} 行)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {Object.keys(previewData.detected_columns).map((col) => (
                    <th
                      key={col}
                      className="px-4 py-2 text-left font-medium text-gray-900"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {previewData.preview_rows.slice(0, 10).map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    {Object.keys(previewData.detected_columns).map((col) => (
                      <td
                        key={`${idx}-${col}`}
                        className="px-4 py-2 text-gray-600"
                      >
                        {row[col] || '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {previewData.preview_rows.length > 10 && (
            <p className="text-xs text-gray-500 mt-2">
              显示前 10 行，共 {previewData.preview_rows.length} 行
            </p>
          )}
        </div>

        {/* Actions */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="flex gap-3">
          <button
            onClick={() => {
              setPreviewData(null);
              setSelectedFile(null);
            }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            返回
          </button>
          <button
            onClick={handleConfirmImport}
            disabled={confirmMutation.isPending}
            className="flex-1 px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {confirmMutation.isPending ? '导入中...' : '确认导入'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Import Section */}
      <div className="bg-white rounded-lg shadow p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">导入参会人</h3>
        <label className="block border-2 border-dashed border-gray-300 rounded-lg p-8 cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition-colors text-center">
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                handleFileSelect(file);
              }
            }}
            disabled={previewMutation.isPending}
            className="hidden"
          />
          <Upload className="mx-auto mb-3 text-gray-400" size={40} />
          <p className="text-base font-medium text-gray-900 mb-1">
            上传 Excel 或 CSV 文件
          </p>
          <p className="text-sm text-gray-500">
            {selectedFile
              ? `已选择: ${selectedFile.name}`
              : '点击选择文件，支持 .xlsx, .xls, .csv'}
          </p>
        </label>

        {previewMutation.isPending && (
          <p className="text-gray-600 mt-3 text-center">处理中...</p>
        )}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 mt-3">
            {error}
          </div>
        )}
      </div>

      {/* Export Section */}
      <div className="bg-white rounded-lg shadow p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">导出数据</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href={apiClient.getExportAttendeesUrl(eventId)}
            className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Download size={24} className="text-indigo-600" />
            <div>
              <p className="font-medium text-gray-900">导出参会人员</p>
              <p className="text-sm text-gray-500">
                包含姓名、职位、组织、状态、座位等信息
              </p>
            </div>
          </a>
          <a
            href={apiClient.getExportSeatmapUrl(eventId)}
            className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Download size={24} className="text-green-600" />
            <div>
              <p className="font-medium text-gray-900">导出座位图</p>
              <p className="text-sm text-gray-500">
                Excel 网格视图，展示各座位分配情况
              </p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
