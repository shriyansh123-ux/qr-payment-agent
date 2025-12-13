export default function ResultCard({ result }) {
  return (
    <div className="card result">
      <h2>Result</h2>

      <p>{result.message}</p>

      <strong>
        Total: ₹{result.total_home?.toFixed(2)}
      </strong>
    </div>
  );
}
