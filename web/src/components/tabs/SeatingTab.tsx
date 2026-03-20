import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Grid3X3, Shuffle, Users, Download } from 'lucide-react';
import { apiClient } from '../../lib/api';

interface SeatingTabProps {
  eventId: string;
  event: {
    venue_rows: number;
    venue_cols: number;
    layout_type: string;
  };
}

interface Seat {
  id: string;
  row_num: number;
  col_num: number;
  label: string;
  seat_type: string;
  attendee_id: string | null;
}

interface Attendee {
  id: string;
  name: string;
  role: string;
  status: string;
}

const LAYOUT_CONFIG: Record<string, {
  label: string;
  description: string;
  seatShape: string;
}> = {
  theater: {
    label: '剧院式',
    description: '面向前方的排列座位',
    seatShape: 'rounded',
  },
  classroom: {
    label: '课桌式',
    description: '带桌子的排列座位',
    seatShape: 'rounded-sm',
  },
  roundtable: {
    label: '圆桌式',
    description: '圆桌分组座位',
    seatShape: 'rounded-full',
  },
  banquet: {
    label: '宴会式',
    description: '宴会桌分组座位',
    seatShape: 'rounded-full',
  },
  u_shape: {
    label: 'U形',
    description: 'U形会议座位',
    seatShape: 'rounded',
  },
};

const SEAT_COLORS: Record<string, string> = {
  normal: 'bg-blue-100 border-blue-300 hover:bg-blue-200',
  vip: 'bg-purple-100 border-purple-300 hover:bg-purple-200',
  reserved: 'bg-yellow-100 border-yellow-300 hover:bg-yellow-200',
  disabled: 'bg-gray-200 border-gray-300 cursor-not-allowed',
  aisle: 'bg-transparent border-transparent',
  occupied: 'bg-green-100 border-green-400',
  occupied_vip: 'bg-purple-200 border-purple-500',
};

export function SeatingTab({ eventId, event }: SeatingTabProps) {
  const [selectedSeat, setSelectedSeat] = useState<Seat | null>(null);
  const [strategy, setStrategy] = useState('vip_first');
  const queryClient = useQueryClient();

  const { data: seats = [], isLoading: seatsLoading } = useQuery({
    queryKey: ['seats', eventId],
    queryFn: async () => {
      const result = await apiClient.getSeats(eventId);
      return ((result as any).data || result) as Seat[];
    },
  });

  const { data: attendees = [] } = useQuery({
    queryKey: ['attendees', eventId],
    queryFn: async () => {
      const result = await apiClient.getAttendees(eventId);
      return ((result as any).data || result) as Attendee[];
    },
  });

  const createGridMutation = useMutation({
    mutationFn: () =>
      apiClient.createSeatGrid(eventId, event.venue_rows, event.venue_cols),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seats', eventId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', eventId] });
    },
  });

  const autoAssignMutation = useMutation({
    mutationFn: () => apiClient.autoAssignSeats(eventId, strategy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seats', eventId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', eventId] });
    },
  });

  // Build attendee lookup
  const attendeeMap = new Map<string, Attendee>();
  (attendees as Attendee[]).forEach((a) => attendeeMap.set(a.id, a));

  // Build seat grid
  const seatGrid: (Seat | null)[][] = [];
  const rows = event.venue_rows || 0;
  const cols = event.venue_cols || 0;

  for (let r = 0; r < rows; r++) {
    seatGrid[r] = [];
    for (let c = 0; c < cols; c++) {
      seatGrid[r][c] = null;
    }
  }

  (seats as Seat[]).forEach((seat) => {
    const r = seat.row_num - 1;
    const c = seat.col_num - 1;
    if (r >= 0 && r < rows && c >= 0 && c < cols) {
      seatGrid[r][c] = seat;
    }
  });

  const layoutConfig = LAYOUT_CONFIG[event.layout_type] || LAYOUT_CONFIG.theater;
  const hasSeats = (seats as Seat[]).length > 0;
  const assignedCount = (seats as Seat[]).filter((s) => s.attendee_id).length;
  const totalSeats = (seats as Seat[]).length;
  const unassignedAttendees = (attendees as Attendee[]).filter(
    (a) =>
      a.status !== 'cancelled' &&
      !(seats as Seat[]).some((s) => s.attendee_id === a.id)
  );

  const getSeatColor = (seat: Seat): string => {
    if (seat.seat_type === 'disabled') return SEAT_COLORS.disabled;
    if (seat.seat_type === 'aisle') return SEAT_COLORS.aisle;
    if (seat.attendee_id) {
      const att = attendeeMap.get(seat.attendee_id);
      if (att && (att.role === 'vip' || att.role === 'speaker')) {
        return SEAT_COLORS.occupied_vip;
      }
      return SEAT_COLORS.occupied;
    }
    return SEAT_COLORS[seat.seat_type] || SEAT_COLORS.normal;
  };

  const getSeatLabel = (seat: Seat): string => {
    if (seat.seat_type === 'aisle') return '';
    if (seat.seat_type === 'disabled') return '×';
    if (seat.attendee_id) {
      const att = attendeeMap.get(seat.attendee_id);
      return att?.name || '已分配';
    }
    return seat.label;
  };

  // Render the visual seat grid based on layout_type
  const renderSeatGrid = () => {
    if (!hasSeats) return null;

    // Calculate seat size based on grid dimensions
    const maxCellSize = Math.min(
      Math.floor(800 / cols),
      Math.floor(500 / rows),
      64
    );
    const cellSize = Math.max(maxCellSize, 32);

    return (
      <div className="overflow-auto">
        {/* Stage / Front indicator */}
        <div className="flex justify-center mb-4">
          <div className="px-16 py-2 bg-gray-800 text-white text-sm rounded-t-lg">
            {event.layout_type === 'roundtable' || event.layout_type === 'banquet'
              ? '入口'
              : '讲台 / 前方'}
          </div>
        </div>

        {/* Seat grid */}
        <div className="flex flex-col items-center gap-1">
          {seatGrid.map((row, rIdx) => (
            <div key={rIdx} className="flex items-center gap-1">
              {/* Row label */}
              <div
                className="text-xs text-gray-500 font-mono text-right"
                style={{ width: '28px' }}
              >
                {String.fromCharCode(65 + rIdx)}
              </div>
              {row.map((seat, cIdx) => {
                if (!seat) {
                  return (
                    <div
                      key={cIdx}
                      style={{ width: cellSize, height: cellSize }}
                      className="border border-dashed border-gray-200 rounded flex items-center justify-center text-xs text-gray-300"
                    >
                      ?
                    </div>
                  );
                }
                const isSelected = selectedSeat?.id === seat.id;
                return (
                  <button
                    key={cIdx}
                    style={{ width: cellSize, height: cellSize }}
                    className={`border-2 ${layoutConfig.seatShape} flex items-center justify-center text-xs font-medium transition-all ${getSeatColor(seat)} ${
                      isSelected ? 'ring-2 ring-indigo-500 ring-offset-1 scale-110' : ''
                    } ${seat.seat_type === 'disabled' || seat.seat_type === 'aisle' ? '' : 'cursor-pointer'}`}
                    onClick={() => {
                      if (seat.seat_type !== 'disabled' && seat.seat_type !== 'aisle') {
                        setSelectedSeat(isSelected ? null : seat);
                      }
                    }}
                    title={`${seat.label}${seat.attendee_id ? ' - ' + (attendeeMap.get(seat.attendee_id)?.name || '') : ''}`}
                  >
                    <span className="truncate px-0.5 leading-tight">
                      {cellSize >= 48
                        ? getSeatLabel(seat)
                        : seat.attendee_id
                          ? getSeatLabel(seat).charAt(0)
                          : seat.label}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
          {/* Column labels */}
          <div className="flex items-center gap-1">
            <div style={{ width: '28px' }} />
            {Array.from({ length: cols }, (_, i) => (
              <div
                key={i}
                style={{ width: cellSize }}
                className="text-xs text-gray-500 font-mono text-center"
              >
                {i + 1}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Layout Info Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              座位布局 — {layoutConfig.label}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {layoutConfig.description} · {rows} 排 × {cols} 列 = {rows * cols} 座
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-green-200 border border-green-400" />
              已分配 ({assignedCount})
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-blue-100 border border-blue-300" />
              空座 ({totalSeats - assignedCount})
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-purple-200 border border-purple-500" />
              VIP/演讲者
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          {!hasSeats && rows > 0 && cols > 0 && (
            <button
              onClick={() => createGridMutation.mutate()}
              disabled={createGridMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50"
            >
              <Grid3X3 size={18} />
              {createGridMutation.isPending ? '生成中...' : '生成座位'}
            </button>
          )}
          {hasSeats && (
            <>
              <div className="flex items-center gap-2">
                <select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="random">随机分配</option>
                  <option value="vip_first">VIP优先（前排居中）</option>
                  <option value="by_department">按部门分组</option>
                </select>
                <button
                  onClick={() => autoAssignMutation.mutate()}
                  disabled={autoAssignMutation.isPending || unassignedAttendees.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50"
                >
                  <Shuffle size={18} />
                  {autoAssignMutation.isPending ? '分配中...' : '自动排座'}
                </button>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Users size={16} />
                待分配: {unassignedAttendees.length} 人
              </div>
              <a
                href={apiClient.getExportSeatmapUrl(eventId)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                <Download size={18} />
                导出座位图
              </a>
            </>
          )}
        </div>
      </div>

      {/* Seat Map Visualization */}
      <div className="bg-white rounded-lg shadow p-6">
        {seatsLoading ? (
          <div className="text-center text-gray-500 py-8">加载中...</div>
        ) : !hasSeats ? (
          <div className="text-center py-12">
            <Grid3X3 size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 mb-2">
              {rows > 0 && cols > 0
                ? '还没有生成座位，点击上方"生成座位"按钮'
                : '请先在设置中配置会场行列数'}
            </p>
          </div>
        ) : (
          renderSeatGrid()
        )}
      </div>

      {/* Selected Seat Detail */}
      {selectedSeat && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">座位详情</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">座位号：</span>
              <span className="font-medium">{selectedSeat.label}</span>
            </div>
            <div>
              <span className="text-gray-500">位置：</span>
              <span className="font-medium">
                第 {selectedSeat.row_num} 排，第 {selectedSeat.col_num} 列
              </span>
            </div>
            <div>
              <span className="text-gray-500">类型：</span>
              <span className="font-medium">{selectedSeat.seat_type}</span>
            </div>
            <div>
              <span className="text-gray-500">入座人：</span>
              <span className="font-medium">
                {selectedSeat.attendee_id
                  ? attendeeMap.get(selectedSeat.attendee_id)?.name || '未知'
                  : '空座'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Auto-assign result feedback */}
      {autoAssignMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
          自动排座完成，共分配 {(autoAssignMutation.data as any)?.count || 0} 个座位
        </div>
      )}
      {autoAssignMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          排座失败：{(autoAssignMutation.error as Error)?.message}
        </div>
      )}
    </div>
  );
}
