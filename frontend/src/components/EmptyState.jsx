export function EmptyState({ message = 'Данные отсутствуют.' }) {
  return <div className="state-block state-block--empty">{message}</div>;
}
