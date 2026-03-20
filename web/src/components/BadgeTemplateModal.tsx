import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { apiClient } from '../lib/api';

interface BadgeTemplate {
  id: string;
  name: string;
  template_type: string;
  html_template: string;
  css: string;
  style_category?: string;
}

interface BadgeTemplateModalProps {
  isOpen: boolean;
  template?: BadgeTemplate | null;
  onClose?: () => void;
  onModalClose: () => void;
}

const TEMPLATE_TYPES = [
  { value: 'badge', label: '胸牌' },
  { value: 'tent_card', label: '桌签' },
];

const STYLE_CATEGORIES = [
  { value: 'business', label: '商务' },
  { value: 'academic', label: '学术' },
  { value: 'government', label: '政府' },
  { value: 'custom', label: '自定义' },
];

const DEFAULT_HTML = `<div class="badge-container">
  <div class="name">{{name}}</div>
  <div class="title">{{title}}</div>
  <div class="organization">{{organization}}</div>
</div>`;

const DEFAULT_CSS = `.badge-container {
  width: 200px;
  height: 300px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px solid #333;
  border-radius: 8px;
  background: white;
  font-family: Arial, sans-serif;
}

.name {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}

.title {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.organization {
  font-size: 12px;
  color: #999;
}`;

export function BadgeTemplateModal({
  isOpen,
  template,
  onClose,
  onModalClose,
}: BadgeTemplateModalProps) {
  const [name, setName] = useState('');
  const [templateType, setTemplateType] = useState('badge');
  const [htmlTemplate, setHtmlTemplate] = useState(DEFAULT_HTML);
  const [css, setCss] = useState(DEFAULT_CSS);
  const [styleCategory, setStyleCategory] = useState('custom');
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!isOpen) return;

    if (template) {
      const updateState = () => {
        setName(template.name);
        setTemplateType(template.template_type);
        setHtmlTemplate(template.html_template);
        setCss(template.css);
        setStyleCategory(template.style_category || 'custom');
        setError('');
      };
      updateState();
    } else {
      const resetState = () => {
        setName('');
        setTemplateType('badge');
        setHtmlTemplate(DEFAULT_HTML);
        setCss(DEFAULT_CSS);
        setStyleCategory('custom');
        setError('');
      };
      resetState();
    }
  }, [template, isOpen]);

  const createMutation = useMutation({
    mutationFn: async () => {
      if (template) {
        return apiClient.updateBadgeTemplate(template.id, {
          name,
          template_type: templateType,
          html_template: htmlTemplate,
          css,
          style_category: styleCategory,
        });
      } else {
        return apiClient.createBadgeTemplate({
          name,
          template_type: templateType,
          html_template: htmlTemplate,
          css,
          style_category: styleCategory,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['badge-templates'] });
      onModalClose();
      if (onClose) onClose();
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '保存失败');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name.trim()) {
      setError('请填写模板名称');
      return;
    }
    createMutation.mutate();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-xl font-bold text-gray-900">
            {template ? '编辑模板' : '新建模板'}
          </h2>
          <button
            onClick={onModalClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              模板名称 *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="输入模板名称"
            />
          </div>

          {/* Type and Category */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                模板类型 *
              </label>
              <select
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {TEMPLATE_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                风格分类
              </label>
              <select
                value={styleCategory}
                onChange={(e) => setStyleCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {STYLE_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* HTML Template */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              HTML 模板 *
            </label>
            <textarea
              value={htmlTemplate}
              onChange={(e) => setHtmlTemplate(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
              placeholder="输入 HTML 模板"
            />
            <p className="text-xs text-gray-500 mt-1">
              支持的变量: {'{'}name{'}'}, {'{'}title{'}'}, {'{'}organization{'}'}
            </p>
          </div>

          {/* CSS */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              CSS 样式 *
            </label>
            <textarea
              value={css}
              onChange={(e) => setCss(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
              placeholder="输入 CSS 样式"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onModalClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {createMutation.isPending
                ? '保存中...'
                : template
                ? '更新'
                : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
