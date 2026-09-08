import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { JointAngleTrajectory } from "../types";

const COLORS: Record<string, string> = {
  left: "#2563eb",
  right: "#dc2626",
};

/**
 * Renders one joint's left/right trajectory over a normalized 0-100%
 * gait cycle. Takes the already-resampled trajectories from the API
 * (see backend/app/gait/angles.py::resample_to_percent_cycle) rather
 * than doing any resampling client-side.
 */
export default function JointAngleChart({
  joint,
  trajectories,
}: {
  joint: "hip" | "knee" | "ankle";
  trajectories: JointAngleTrajectory[];
}) {
  const relevant = trajectories.filter((t) => t.joint === joint);
  if (relevant.length === 0) return null;

  // Recharts wants one array of point objects, not per-series arrays.
  const pointCount = relevant[0].percent_gait_cycle.length;
  const data = Array.from({ length: pointCount }, (_, i) => {
    const point: Record<string, number> = { percent: relevant[0].percent_gait_cycle[i] };
    for (const t of relevant) {
      point[t.side] = t.angle_degrees[i];
    }
    return point;
  });

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="mb-2 text-sm font-medium capitalize text-slate-700">{joint} angle (° flexion)</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="percent"
            tickFormatter={(v) => `${v}%`}
            fontSize={11}
            label={{ value: "Gait cycle", position: "insideBottom", offset: -2, fontSize: 11 }}
          />
          <YAxis fontSize={11} width={35} />
          <Tooltip formatter={(v: number) => `${v.toFixed(1)}°`} labelFormatter={(v) => `${v}% of cycle`} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {relevant.map((t) => (
            <Line
              key={t.side}
              type="monotone"
              dataKey={t.side}
              stroke={COLORS[t.side]}
              dot={false}
              strokeWidth={2}
              name={t.side}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
