import { useId, useState } from "react";

const outcomes = {
  success: "Simulation successful — no money moved.",
  declined: "Simulation declined — no money moved.",
  timeout: "Simulation timed out — no payment was attempted.",
};

export default function PaymentSimulation({ amount, currency, fees }) {
  const id = useId();
  const [stage, setStage] = useState("idle");
  const [outcome, setOutcome] = useState("success");
  const money = value => `${currency} ${Number(value).toFixed(2)}`;
  const finished = stage === "complete" || stage === "cancelled";
  return <section className="paymentSimulation" aria-labelledby={`${id}-title`}>
    <span className="simulationBadge">SIMULATION · NO REAL PAYMENT</span>
    <h3 id={`${id}-title`}>Payment simulation</h3>
    <p className="hintText">Explore the proposed approval flow with your estimate. No payment app opens, no bank is contacted, and no money is deducted. No PIN or bank details are needed.</p>
    {stage === "idle" ? <button className="btnSecondary" type="button" onClick={() => setStage("review")}>Start payment simulation</button> : <>
      <ol className="simulationSteps" aria-label="Simulation progress">
        <li aria-current={stage === "review" ? "step" : undefined}>1. Review estimate</li>
        <li aria-current={stage === "pending" ? "step" : undefined}>2. Simulated approval</li>
        <li aria-current={finished ? "step" : undefined}>3. Simulated status</li>
      </ol>
      <dl className="insightFacts">
        <div><dt>Reference amount</dt><dd>{money(amount)}</dd></div>
        <div><dt>Your assumed fees</dt><dd>{money(fees)}</dd></div>
        <div><dt>Simulation total</dt><dd>{money(amount + fees)}</dd></div>
      </dl>
      <p className="hint">This uses the combined QR estimate and adds the fixed fee once. It is not a bank quote or a merchant receipt. Editing the estimate or fees resets this simulation.</p>
      {stage === "review" && <>
        <label className="label" htmlFor={`${id}-outcome`}>Demo outcome</label>
        <select className="textarea" id={`${id}-outcome`} value={outcome} onChange={event => setOutcome(event.target.value)}>
          <option value="success">Simulated success</option>
          <option value="declined">Simulated decline</option>
          <option value="timeout">Simulated timeout</option>
        </select>
        <div className="actions">
          <button className="btnPrimary" type="button" onClick={() => setStage("pending")}>Approve simulation</button>
          <button className="btnSecondary" type="button" onClick={() => setStage("cancelled")}>Cancel simulation</button>
        </div>
      </>}
      {stage === "pending" && <>
        <p role="status">Simulation pending. In a real integration, approval and confirmed status would come from the payment provider.</p>
        <div className="actions">
          <button className="btnPrimary" type="button" onClick={() => setStage("complete")}>Show simulated result</button>
          <button className="btnSecondary" type="button" onClick={() => setStage("cancelled")}>Cancel simulation</button>
        </div>
      </>}
      {finished && <>
        <p className="simulationStatus" role="status">{stage === "cancelled"
          ? "Simulation cancelled — no payment was attempted." : outcomes[outcome]}</p>
        <button className="btnSecondary" type="button" onClick={() => { setStage("idle"); setOutcome("success"); }}>Reset simulation</button>
      </>}
    </>}
    <p className="hint">Simulation state stays in this page only and is never saved as a transaction or account payment status.</p>
  </section>;
}
