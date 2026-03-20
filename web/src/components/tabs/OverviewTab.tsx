import { useQuery } from '@tanstack/react-query';
import { Users, CheckCircle, Star, Eye } from 'lucide-react';
import { apiClient } from '../../lib/api';

interface OverviewTabProps {
  eventId: string;
}

interface DashboardStats {
  total_attendees: number;
  checked_in_count: number;
  pending_count: number;
  absent_count: number;
  cancelled_count: number;
  checkin_rate: number;
  high_priority_count: number;
  mid_priority_count: number;
  seats_total: number;
  seats_occupied: number;
  seats_available: number;
  seat_utilization_rate: number;
}

export function OverviewTab({ eventId }: OverviewTabProps) {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard', eventId],
    queryFn: () => apiClient.getDashboard(eventId) as Promise<DashboardStats>,
  });

  if (isLoading) {
    return <div className="text-center text-gray-500 py-8">加载中...</div>;
  }

  if (!stats) {
    return <div className="text-center text-gray-500 py-8">无数据</div>;
  }

  const StatCard = ({
    icon: Icon,
    label,
    value,
    unit = '',
    color = 'indigo',
  }: {
    icon: any;
    label: string;
    value: string | number;
    unit?: string;
    color?: string;
  }) => {
    const colorClasses = {
      indigo: 'bg-indigo-50 text-indigo-600',
      green: 'bg-green-50 text-green-600',
      blue: 'bg-blue-50 text-blue-600',
      purple: 'bg-purple-50 text-purple-600',
    };

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-2">{label}</p>
            <p className="text-3xl font-bold text-gray-900">
              {value}
              {unit && <span className="text-lg ml-1">{unit}</span>}
            </p>
          </div>
          <div className={`${colorClasses[color as keyof typeof colorClasses]} p-3 rounded-lg`}>
            <Icon size={24} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="总参会人数"
          value={stats.total_attendees}
          color="indigo"
        />
        <StatCard
          icon={CheckCircle}
          label="已签到"
          value={stats.checked_in_count}
          color="green"
        />
        <StatCard
          icon={Star}
          label="重要嘉宾"
          value={stats.high_priority_count}
          color="purple"
        />
        <StatCard
          icon={Eye}
          label="签到率"
          value={(stats.checkin_rate * 100).toFixed(1)}
          unit="%"
          color="blue"
        />
      </div>

      {/* Checkin Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">签到状态分布</h3>
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">已签到</span>
              <span className="font-medium text-gray-900">{stats.checked_in_count}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{
                  width: `${
                    stats.total_attendees > 0
                      ? (stats.checked_in_count / stats.total_attendees) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">待签到</span>
              <span className="font-medium text-gray-900">{stats.pending_count}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-yellow-600 h-2 rounded-full"
                style={{
                  width: `${
                    stats.total_attendees > 0
                      ? (stats.pending_count / stats.total_attendees) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">缺席</span>
              <span className="font-medium text-gray-900">{stats.absent_count}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gray-600 h-2 rounded-full"
                style={{
                  width: `${
                    stats.total_attendees > 0
                      ? (stats.absent_count / stats.total_attendees) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Seat Usage */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">座位使用情况</h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">座位利用率</span>
              <span className="font-medium text-gray-900">
                {(stats.seat_utilization_rate * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full"
                style={{
                  width: `${stats.seat_utilization_rate * 100}%`,
                }}
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-indigo-600">{stats.seats_occupied}</p>
              <p className="text-xs text-gray-600">已占用</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{stats.seats_available}</p>
              <p className="text-xs text-gray-600">可用</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-600">{stats.seats_total}</p>
              <p className="text-xs text-gray-600">总计</p>
            </div>
          </div>
        </div>
      </div>

      {/* Participant Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">参会者优先级分布</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-amber-50 rounded-lg">
            <p className="text-sm text-amber-600 mb-1">高优先级 (≥10)</p>
            <p className="text-2xl font-bold text-amber-900">{stats.high_priority_count}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-600 mb-1">中优先级 (1-9)</p>
            <p className="text-2xl font-bold text-blue-900">{stats.mid_priority_count}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
