import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Edit } from 'lucide-react';
import { apiClient } from '../lib/api';
import { BadgeTemplateModal } from '../components/BadgeTemplateModal';

interface BadgeTemplate {
  id: string;
  name: string;
  template_type: string;
  html_template: string;
  css: string;
  is_builtin: boolean;
  style_category?: string;
}

const TEMPLATE_TYPES = [
  { value: 'badge', label: '胸牌' },
  { value: 'tent_card', label: '桌签' },
];

export function BadgeTemplatesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<BadgeTemplate | null>(null);
  const [templateTypeFilter, setTemplateTypeFilter] = useState('');
  const queryClient = useQueryClient();

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['badge-templates', templateTypeFilter],
    queryFn: async () => {
      const result = await apiClient.getBadgeTemplates(
        templateTypeFilter || undefined
      );
      return (result as any).data || result;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (templateId: string) =>
      apiClient.deleteBadgeTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['badge-templates'] });
    },
  });

  const handleDelete = (templateId: string, templateName: string) => {
    if (confirm(`确定要删除模板 "${templateName}" 吗？`)) {
      deleteMutation.mutate(templateId);
    }
  };

  const handleEditClose = () => {
    setSelectedTemplate(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">模板管理</h1>
          <p className="text-gray-600 mt-1">管理胸牌和桌签模板</p>
        </div>
        <button
          onClick={() => {
            setSelectedTemplate(null);
            setShowCreateModal(true);
          }}
          className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
        >
          <Plus size={20} />
          新建模板
        </button>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        <select
          value={templateTypeFilter}
          onChange={(e) => setTemplateTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">全部类型</option>
          {TEMPLATE_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full text-center text-gray-500 py-8">
            加载中...
          </div>
        ) : (templates as BadgeTemplate[]).length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-8">
            还没有模板
          </div>
        ) : (
          (templates as BadgeTemplate[]).map((template) => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden"
            >
              {/* Preview */}
              <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center overflow-hidden">
                <div
                  className="w-full h-full flex items-center justify-center text-white text-center p-4"
                  dangerouslySetInnerHTML={{ __html: template.html_template }}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  }}
                />
              </div>

              {/* Info */}
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {template.name}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {TEMPLATE_TYPES.find((t) => t.value === template.template_type)
                        ?.label || template.template_type}
                    </p>
                  </div>
                  {template.is_builtin && (
                    <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                      内置
                    </span>
                  )}
                </div>

                {/* Category */}
                {template.style_category && (
                  <p className="text-xs text-gray-600 mb-3">
                    分类: {template.style_category}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setSelectedTemplate(template);
                      setShowCreateModal(true);
                    }}
                    disabled={template.is_builtin}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Edit size={16} />
                    编辑
                  </button>
                  <button
                    onClick={() =>
                      handleDelete(template.id, template.name)
                    }
                    disabled={template.is_builtin || deleteMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Trash2 size={16} />
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      <BadgeTemplateModal
        isOpen={showCreateModal}
        template={selectedTemplate}
        onClose={handleEditClose}
        onModalClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
