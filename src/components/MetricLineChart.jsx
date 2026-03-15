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

export function MetricLineChart({ data, xKey, lines, height = 320 }) {
  const minChartWidth = Math.max(520, (Array.isArray(data) ? data.length : 0) * 90);

  return (
    <div className="chart-card">
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <div style={{ width: '100%', minWidth: minChartWidth, height }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              {lines.map((line) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  name={line.name}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}