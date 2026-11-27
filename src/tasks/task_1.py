import time

from src.models import CASES, StepMetric


async def run_task1(workflows):
    rows = []
    for case in CASES:
        for workflow_name in ("one_shot", "sequential"):
            trace: list[StepMetric] = []
            started = time.perf_counter()
            incident = None
            error = None
            try:
                workflow = getattr(
                    workflows,
                    workflow_name
                )

                incident = await workflow(
                    case["text"],
                    trace,
                    use_retry=False,
                )

            except Exception as exc:
                error = f"{type(exc).__name__}: {str(exc)[:250]}"
            wall_time = time.perf_counter() - started
            prompt_tokens = sum(
                x.prompt_tokens or 0
                for x in trace
            )
            completion_tokens = sum(
                x.completion_tokens or 0
                for x in trace
            )
            rows.append({
                "case": case["id"],
                "workflow": workflow_name,
                "success": int(incident is not None and error is None),
                "cat_acc": int(
                    incident is not None
                    and incident.category == case["category_true"]
                ),
                "sev_acc": int(
                    incident is not None
                    and incident.severity == case["severity_true"]
                ),
                "imp_acc": int(
                    incident is not None
                    and incident.impact == case["impact_true"]
                ),
                "wall_s": round(wall_time, 3),
                "calls": len(trace),
                "tokens": prompt_tokens + completion_tokens,
                "error": error
            })

    grouped = {}
    for row in rows:
        name = row["workflow"]
        grouped.setdefault(name, []).append(row)

    summary = []
    for workflow_name, items in grouped.items():
        n = len(items)
        summary.append({
            "workflow": workflow_name,
            "cases": n,
            "success_rate": round(sum(x["success"] for x in items) / n, 3),
            "category_accuracy": round(sum(x["cat_acc"] for x in items) / n, 3),
            "severity_accuracy": round(sum(x["sev_acc"] for x in items) / n, 3),
            "impact_accuracy": round(sum(x["imp_acc"] for x in items) / n, 3),
            "mean_wall_s": round(sum(x["wall_s"] for x in items) / n, 3),
            "mean_calls": round(sum(x["calls"] for x in items) / n, 3),
            "mean_tokens": round(sum(x["tokens"] for x in items) / n, 3)
        })

    return rows, summary
