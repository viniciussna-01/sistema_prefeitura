import { Badge } from "@/components/ui";
import { ExecutionStatus, STATUS_LABELS } from "@/lib/types";

const tones: Record<ExecutionStatus, "neutral" | "blue" | "green" | "amber" | "red"> = {
  pending: "neutral",
  dispatched: "blue",
  running: "amber",
  success: "green",
  failed: "red",
  cancelled: "neutral",
};

export function StatusBadge({ status }: { status: ExecutionStatus }) {
  return <Badge tone={tones[status]}>{STATUS_LABELS[status]}</Badge>;
}
