import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
} from 'recharts';

function wrapLabel(text, maxLineLength = 26) {
  if (!text) return ['—'];

  const words = String(text).split(' ');
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    const nextLine = currentLine ? `${currentLine} ${word}` : word;

    if (nextLine.length <= maxLineLength) {
      currentLine = nextLine;
    } else {
      if (currentLine) {
        lines.push(currentLine);
      }
      currentLine = word;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines;
}

function getMaxLines(data, key, maxLineLength) {
  if (!Array.isArray(data) || !data.length) return 1;

  return data.reduce((max, item) => {
    const lines = wrapLabel(item?.[key], maxLineLength).length;
    return Math.max(max, lines);
  }, 1);
}

function getYAxisWidth(data, key) {
  if (!Array.isArray(data) || !data.length) return 260;

  const longest = data.reduce((max, item) => {
    const len = String(item?.[key] ?? '').length;
    return Math.max(max, len);
  }, 0);

  if (longest > 70) return 420;
  if (longest > 56) return 360;
  if (longest > 42) return 320;
  if (longest > 30) return 280;

  return 240;
}

function CustomYAxisTick(props) {
  const { x, y, payload, maxLineLength = 26 } = props;
  const lines = wrapLabel(payload.value, maxLineLength);

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        textAnchor="end"
        fill="#5b6475"
        fontSize={14}
        dy={4}
      >
        {lines.map((line, index) => (
          <tspan
            key={`${line}-${index}`}
            x={0}
            dy={index === 0 ? 0 : 16}
          >
            {line}
          </tspan>
        ))}
      </text>
    </g>
  );
}

export function SimpleComparisonChart({
  data = [],
  dataKey,
  yKey = 'name',
  height,
  valueFormatter = (value) => String(value),
}) {
  const maxLineLength = 26;
  const maxLines = getMaxLines(data, yKey, maxLineLength);
  const yAxisWidth = getYAxisWidth(data, yKey);
  const rowHeight = Math.max(48, maxLines * 18 + 20);
  const calculatedHeight = Math.max(240, data.length * rowHeight + 40);
  const finalHeight = height || calculatedHeight;

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={finalHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 80, left: 12, bottom: 8 }}
          barCategoryGap={16}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            fontSize={14}
            tickFormatter={(value) => valueFormatter(Number(value))}
          />
          <YAxis
            type="category"
            dataKey={yKey}
            width={yAxisWidth}
            axisLine={false}
            tickLine={false}
            interval={0}
            tick={<CustomYAxisTick maxLineLength={maxLineLength} />}
          />
          <Tooltip
            formatter={(value) => [valueFormatter(Number(value)), 'Значение']}
            cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
          />
          <Bar
            dataKey={dataKey}
            radius={[0, 6, 6, 0]}
            maxBarSize={28}
          >
            <LabelList
              dataKey={dataKey}
              position="right"
              formatter={(value) => valueFormatter(Number(value))}
              style={{
                fill: '#7a6b5d',
                fontSize: 14,
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}