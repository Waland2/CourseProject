import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';

const DEFAULT_COLORS = ['#1f4ed8', '#16a34a', '#d97706', '#9333ea', '#dc2626'];

function truncateLabel(text, maxLength = 26) {
  if (!text) return '—';
  const value = String(text).trim();
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength - 1)}…`;
}

function CustomYAxisTick(props) {
  const { x, y, payload } = props;
  const label = truncateLabel(payload.value, 28);

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        dy={4}
        textAnchor="end"
        fill="#5b6475"
        fontSize={14}
      >
        {label}
      </text>
    </g>
  );
}

export function MetricComparisonChart({
  data = [],
  series = [],
  height = 420,
}) {
  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 180, bottom: 8 }}
          barCategoryGap={18}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
            axisLine={false}
            tickLine={false}
            fontSize={14}
          />
          <YAxis
            type="category"
            dataKey="metric"
            width={170}
            axisLine={false}
            tickLine={false}
            interval={0}
            tick={<CustomYAxisTick />}
          />
          <Tooltip
            formatter={(value, name, context) => {
              const rawKey = `${context.dataKey}_raw`;
              const rawValue = context.payload?.[rawKey];
              const normalized = `${Number(value).toFixed(1)}%`;

              if (rawValue === null || rawValue === undefined || rawValue === '') {
                return [normalized, name];
              }

              return [`${normalized} · факт: ${rawValue}`, name];
            }}
          />
          <Legend />
          {series.map((item, index) => (
            <Bar
              key={item.dataKey}
              dataKey={item.dataKey}
              name={item.name}
              radius={[0, 6, 6, 0]}
              maxBarSize={18}
            >
              {data.map((entry, cellIndex) => (
                <Cell
                  key={`${item.dataKey}-${cellIndex}`}
                  fill={item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                />
              ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}