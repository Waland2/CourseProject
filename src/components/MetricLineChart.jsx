import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const DEFAULT_LINE_COLORS = ['#2563eb', '#d97706'];

function useViewportWidth() {
  const getWidth = () =>
    typeof window !== 'undefined' ? window.innerWidth : 1280;

  const [width, setWidth] = useState(getWidth);

  useEffect(() => {
    const onResize = () => setWidth(getWidth());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return width;
}

export function MetricLineChart({ data, xKey, lines, height = 320 }) {
  const viewportWidth = useViewportWidth();
  const isMobile = viewportWidth <= 560;
  const pointsCount = Array.isArray(data) ? data.length : 0;

  const minChartWidth = isMobile
    ? Math.max(360, pointsCount * 56)
    : '100%';

  return (
    <div className="chart-card">
      <div style={{ width: '100%', overflowX: isMobile ? 'auto' : 'hidden' }}>
        <div style={{ width: '100%', minWidth: minChartWidth, height }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 8,
                right: isMobile ? 12 : 16,
                left: isMobile ? 0 : 8,
                bottom: 8,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} tick={{ fontSize: isMobile ? 12 : 14 }} />
              <YAxis tick={{ fontSize: isMobile ? 12 : 14 }} width={isMobile ? 36 : 48} />
              <Tooltip />
              <Legend />
              {lines.map((line, index) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  name={line.name}
                  stroke={line.color || DEFAULT_LINE_COLORS[index % DEFAULT_LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: isMobile ? 3 : 4 }}
                  activeDot={{ r: isMobile ? 5 : 6 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}