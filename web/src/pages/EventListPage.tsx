import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Copy, ChevronRight } from 'lucide-react';
import { apiClient } from '../lib/api';
import { CreateEventModal } from '../components/CreateEventModal';

const STATUS_LABELS = {
  draft: { label: '草稿', color: 'bg-gray-100 text-gray-800' },
  active: { label: '进行中', color: 'bg-blue-100 text-blue-800' },
  completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
  cancelled: { label: '已取消', color: 'bg-red-100 text-red-800' },
};

export function EventListPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: events = [], isLoading } = useQuery({
    queryKey: ['events', statusFilter],
    queryFn: async () => {
      const result = await apiClient.getEvents(
        statusFilter !== 'all' ? statusFilter : undefined
      );
      return (result as any).data || result;
    },
  });

  const deleteEventMutation = useMutation({
    mutationFn: (eventId: string) => apiClient.deleteEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });

  const duplicateEventMutation = useMutation({
    mutationFn: (eventId: string) => apiClient.duplicateEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });

  const handleDelete = (eventId: string, eventName: string) => {
    if (confirm(`确定要删除活动 "${eventName}" 吗？`)) {
      deleteEventMutation.mutate(eventId);
    }
  };

  const handleDuplicate = (eventId: string) => {
    duplicateEventMutation.mutate(eventId);
  };

  const statuses = ['all', 'draft', 'active', 'completed', 'cancelled'] as const;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">活动管理</h1>
          <p className="text-gray-600 mt-1">管理和组织您的所有活动</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
        >
          <Plus size={20} />
          新建活动
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {statuses.map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              statusFilter === status
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {status === 'all' ? '全部' : STATUS_LABELS[status as keyof typeof STATUS_LABELS].label}
          </button>
        ))}
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            还没有活动，点击"新建活动"开始
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">活动名称</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">日期</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">地点</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">场景</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">状态</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(events as any[]).map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50 transition-colors">
                    <td
                      className="px-6 py-4 text-sm font-medium text-gray-900 cursor-pointer"
                      onClick={() => navigate(`/events/${event.id}`)}
                    >
                      {event.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {event.event_date ? new Date(event.event_date).toLocaleDateString('zh-CN') : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {event.location || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {event.layout_type || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                          STATUS_LABELS[event.status as keyof typeof STATUS_LABELS]
                            ?.color || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {STATUS_LABELS[event.status as keyof typeof STATUS_LABELS]?.label || event.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate(`/events/${event.id}`)}
                          className="p-1 hover:bg-gray-100 rounded transition-colors"
                          title="查看详情"
                        >
                          <ChevronRight size={18} className="text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleDuplicate(event.id)}
                          disabled={duplicateEventMutation.isPending}
                          className="p-1 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                          title="复制活动"
                        >
                          <Copy size={18} className="text-gray-600" />
                        </button>
                        {event.status === 'draft' && (
                          <button
                            onClick={() => handleDelete(event.id, event.name)}
                            disabled={deleteEventMutation.isPending}
                            className="p-1 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                            title="删除活动"
                          >
                            <Trash2 size={18} className="text-red-600" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <CreateEventModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
