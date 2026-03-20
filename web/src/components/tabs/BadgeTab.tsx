/**
 * BadgeTab — Badge/nameplate design with sub-agent.
 *
 * Left side: template gallery + preview
 * Right side: sub-agent for iterating on badge design
 */
import { useQuery } from '@tanstack/react-query';
import { Tag, CreditCard, Palette } from 'lucide-react';
import { apiClient } from '../../lib/api';
import { SubAgentPanel } from '../SubAgentPanel';

interface BadgeTabProps {
  eventId: string;
}

interface BadgeTemplate {
  id: string;
  name: string;
  template_type: string;
  style_category: string;
  is_builtin: boolean;
}

const STYLE_COLORS: Record<string, string> = {
  business: 'bg-blue-100 text-blue-700',
  academic: 'bg-purple-100 text-purple-700',
  government: 'bg-red-100 text-red-700',
  custom: 'bg-gray-100 text-gray-700',
};

export function BadgeTab({ eventId }: BadgeTabProps) {
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['badge-templates'],
    queryFn: () => apiClient.getBadgeTemplates() as Promise<BadgeTemplate[]>,
  });

  const badges = (templates as BadgeTemplate[]).filter((t) => t.template_type === 'badge');
  const tentCards = (templates as BadgeTemplate[]).filter((t) => t.template_type === 'tent_card');

  return (
    <div className="flex h-[calc(100vh-240px)] -mx-4 -mb-4">
      {/* Left: Template gallery */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Badges */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Tag size={20} className="text-indigo-600" />
            胸牌模板
          </h3>
          {isLoading ? (
            <div className="text-gray-500 text-sm">加载中...</div>
          ) : badges.length === 0 ? (
            <div className="bg-gray-50 rounded-xl p-8 text-center">
              <Palette size={40} className="mx-auto mb-3 text-gray-300" />
              <p className="text-sm text-gray-500">还没有胸牌模板</p>
              <p className="text-xs text-gray-400 mt-1">
                告诉右侧 AI 助手你想要什么风格的胸牌
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {badges.map((t) => (
                <div key={t.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="w-full h-24 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg mb-3 flex items-center justify-center">
                    <CreditCard size={32} className="text-indigo-300" />
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate">{t.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${STYLE_COLORS[t.style_category] || STYLE_COLORS.custom}`}>
                      {t.style_category}
                    </span>
                    {t.is_builtin && <span className="text-[10px] text-gray-400">内置</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tent Cards */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <CreditCard size={20} className="text-green-600" />
            桌签模板
          </h3>
          {tentCards.length === 0 ? (
            <div className="bg-gray-50 rounded-xl p-6 text-center">
              <p className="text-sm text-gray-500">还没有桌签模板</p>
              <p className="text-xs text-gray-400 mt-1">AI 助手可以帮你设计</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {tentCards.map((t) => (
                <div key={t.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="w-full h-16 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg mb-3 flex items-center justify-center">
                    <CreditCard size={28} className="text-green-300" />
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate">{t.name}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Sub-agent */}
      <SubAgentPanel
        eventId={eventId}
        scope="badge"
        title="铭牌设计助手"
        placeholder="描述你想要的铭牌风格..."
        welcomeMessage={
          '我是铭牌设计助手。我可以帮你：\n\n' +
          '· 设计胸牌/桌签模板\n' +
          '· 上传参考图片选择风格\n' +
          '· 批量生成 PDF 打印\n' +
          '· 中英双语铭牌\n\n' +
          '告诉我你想要什么风格？'
        }
      />
    </div>
  );
}
