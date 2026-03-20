export function ErrorState({ message = 'Не удалось загрузить данные.' }) {
  return <div className="state-block state-block--error">{message}</div>;
}
