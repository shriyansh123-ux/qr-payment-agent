export default function HistoryTable({ rows }) {
  if (!rows.length) return null;

  return (
    <div className="card">
      <h2>History</h2>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Input</th>
            <th>Total (INR)</th>
            <th>Risk</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.time}</td>
              <td>{r.input}</td>
              <td>{r.total}</td>
              <td>{r.risk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
