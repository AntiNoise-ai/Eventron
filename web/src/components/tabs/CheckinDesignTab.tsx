/**
 * CheckinDesignTab — Check-in page design with sub-agent.
 *
 * Left: checkin page preview + settings
 * Right: sub-agent for designing the check-in experience
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  QrCode, Smartphone, Clock, Users, CheckCircle, Settings2
} from 'lucide-react';
import { apiClient } from '../../lib/api';
import { SubAgentPanel } from '../SubAgentPanel';

interface CheckinDesignTabProps {
  eventId: string;
}

interface DashboardStats {
  total_attendees: number;
  checked_in_count: number;
  checkin_rate: number;
}

export function CheckinDesignTab({ eventId }: CheckinDesignTabProps) {
  const [checkinMode, setCheckinMode] = useState('qr');

  const { data: stats } = useQuery({
    queryKey: ['dashboard', eventId],
    queryFn: () => apiClient.getDashboard(eventId) as Promise<DashboardStats>,
  });

  return (
    <div className="flex h-[calc(100vh-240px)] -mx-4 -mb-4">
      {/* Left: Checkin setup */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Live Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <Users size={20} className="mx-auto text-indigo-500 mb-1" />
              <p className="text-2xl font-bold text-gray-900">{stats.total_attendees}</p>
              <p className="text-xs text-gray-500">总人数</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <CheckCircle size={20} className="mx-auto text-green-500 mb-1" />
              <p className="text-2xl font-bold text-green-600">{stats.checked_in_count}</p>
              <p className="text-xs text-gray-500">已签到</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <Clock size={20} className="mx-auto text-blue-500 mb-1" />
              <p className="text-2xl font-bold text-blue-600">{(stats.checkin_rate * 100).toFixed(0)}%</p>
              <p className="text-xs text-gray-500">签到率</p>
            </div>
          </div>
        )}

        {/* Checkin Mode Selector */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Settings2 size={18} className="text-indigo-600" />
            签到方式
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setCheckinMode('qr')}
              className={`p-4 rounded-lg border-2 text-center transition-all ${
                checkinMode === 'qr'
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <QrCode size={28} className={`mx-auto mb-2 ${checkinMode === 'qr' ? 'text-indigo-600' : 'text-gray-400'}`} />
              <p className="text-sm font-medium">扫码签到</p>
              <p className="text-[10px] text-gray-500 mt-1">参会者扫二维码自助签到</p>
            </button>
            <button
              onClick={() => setCheckinMode('name')}
              className={`p-4 rounded-lg border-2 text-center transition-all ${
                checkinMode === 'name'
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Users size={28} className={`mx-auto mb-2 ${checkinMode === 'name' ? 'text-indigo-600' : 'text-gray-400'}`} />
              <p className="text-sm font-medium">姓名签到</p>
              <p className="text-[10px] text-gray-500 mt-1">工作人员搜索姓名签到</p>
            </button>
          </div>
        </div>

        {/* H5 Page Preview */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Smartphone size={18} className="text-indigo-600" />
            签到页预览
          </h3>
          <div className="mx-auto w-48 h-80 bg-gray-100 rounded-2xl border-4 border-gray-800 overflow-hidden relative">
            <div className="absolute top-0 left-0 right-0 h-6 bg-gray-800 flex items-center justify-center">
              <div className="w-16 h-1.5 bg-gray-600 rounded-full" />
            </div>
            <div className="pt-8 px-3 text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full mx-auto mb-2 flex items-center justify-center">
                <QrCode size={24} className="text-indigo-500" />
              </div>
              <p className="text-[10px] font-semibold text-gray-800 mb-1">活动签到</p>
              <p className="text-[8px] text-gray-500 mb-3">请扫描二维码完成签到</p>
              <div className="w-20 h-20 bg-white border border-gray-300 rounded mx-auto mb-2 flex items-center justify-center">
                <QrCode size={40} className="text-gray-300" />
              </div>
              <p className="text-[8px] text-gray-400">等待签到...</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 text-center mt-3">
            告诉 AI 助手你想要的签到页风格，生成 H5 页面
          </p>
        </div>
      </div>

      {/* Right: Sub-agent */}
      <SubAgentPanel
        eventId={eventId}
        scope="checkin"
        title="签到设计助手"
        placeholder="描述签到流程需求..."
        welcomeMessage={
          '我是签到系统设计助手。我可以帮你：\n\n' +
          '· 设计 H5 签到页面\n' +
          '· 设置签到方式（扫码/姓名/人脸）\n' +
          '· 生成签到二维码\n' +
          '· 自定义签到确认页面\n\n' +
          '你想设计什么样的签到体验？'
        }
      />
    </div>
  );
}
