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

function wrapLabel(text, maxLineLength = 18) {
  if (!text) return [''];

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

function getMaxLines(data, xKey, maxLineLength) {
  if (!Array.isArray(data) || data.length === 0) return 1;

  return data.reduce((max, item) => {
    const lines = wrapLabel(item?.[xKey], maxLineLength).length;
    return Math.max(max, lines);
  }, 1);
}

function getYAxisWidth(data, xKey) {
  if (!Array.isArray(data) || data.length === 0) return 140;

  const longest = data.reduce((max, item) => {
    const len = String(item?.[xKey] ?? '').length;
    return Math.max(max, len);
  }, 0);

  if (longest > 40) return 240;
  if (longest > 32) return 220;
  if (longest > 26) return 200;
  if (longest > 20) return 180;

  return 150;
}

function CustomYAxisTick(props) {
  const { x, y, payload, maxLineLength = 18 } = props;
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

export function MetricBarChart({
  data = [],
  xKey,
  bars = [],
  layout = 'horizontal',
  height,
  valueFormatter = (value) => String(value),
}) {
  const isHorizontal = layout === 'horizontal';

  const maxLineLength = 18;
  const maxLines = getMaxLines(data, xKey, maxLineLength);
  const yAxisWidth = getYAxisWidth(data, xKey);

  const rowHeight = Math.max(42, maxLines * 18 + 18);
  const calculatedHeight = Math.max(360, data.length * rowHeight + 40);
  const finalHeight = height || calculatedHeight;

  const minChartWidth = isHorizontal
    ? Math.max(520, yAxisWidth + 260)
    : Math.max(520, data.length * 72);

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <div style={{ width: '100%', minWidth: minChartWidth, height: finalHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout={isHorizontal ? 'vertical' : 'horizontal'}
            margin={{
              top: 8,
              right: 44,
              left: isHorizontal ? 12 : 8,
              bottom: isHorizontal ? 8 : 24,
            }}
            barCategoryGap={12}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />

            {isHorizontal ? (
              <>
                <XAxis
                  type="number"
                  tickFormatter={(value) => valueFormatter(Number(value))}
                  axisLine={false}
                  tickLine={false}
                  fontSize={14}
                />
                <YAxis
                  type="category"
                  dataKey={xKey}
                  width={yAxisWidth}
                  axisLine={false}
                  tickLine={false}
                  interval={0}
                  tick={<CustomYAxisTick maxLineLength={maxLineLength} />}
                />
              </>
            ) : (
              <>
                <XAxis
                  type="category"
                  dataKey={xKey}
                  axisLine={false}
                  tickLine={false}
                  fontSize={14}
                />
                <YAxis
                  type="number"
                  tickFormatter={(value) => valueFormatter(Number(value))}
                  axisLine={false}
                  tickLine={false}
                  fontSize={14}
                />
              </>
            )}

            <Tooltip
              formatter={(value, name) => [
                valueFormatter(Number(value)),
                name,
              ]}
              cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
            />

            {bars.map((bar) => (
              <Bar
                key={bar.dataKey}
                dataKey={bar.dataKey}
                name={bar.name}
                radius={isHorizontal ? [0, 6, 6, 0] : [6, 6, 0, 0]}
                maxBarSize={28}
              >
                <LabelList
                  dataKey={bar.dataKey}
                  position={isHorizontal ? 'right' : 'top'}
                  formatter={(value) => valueFormatter(Number(value))}
                  style={{
                    fill: '#7a6b5d',
                    fontSize: 14,
                  }}
                />
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}