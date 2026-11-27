from src.llm.prompts import CLASSIFY_TASK
from src.models import CASES, Classification, StepMetric


async def run_task2(llm_client):
    detailed = []
    for case in CASES:
        trace: list[StepMetric] = []
        result = None
        error = None
        try:
            result = await llm_client.ask_json_with_retry(
                schema=Classification,
                instruction=CLASSIFY_TASK,
                data={
                    "id": case["id"],
                    "incident_text": case["text"],
                },
                stage="structured_output_retry",
                trace=trace,
                max_retries=2,
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {str(exc)[:300]}"
        metric = trace[0]
        detailed.append({
            "case": case["id"],
            "json_valid": int(result is not None),
            "pydantic_valid": int(result is not None),
            "success": int(metric.success),
            "attempts": metric.attempts,
            "retries": metric.retries,
            "time_s": metric.latency_s,
            "prompt_tokens": metric.prompt_tokens,
            "completion_tokens": metric.completion_tokens,
            "total_tokens": metric.total_tokens,
            "error": error or metric.error,

        })
    n = len(detailed)
    summary = [{
        "experiment": "JSON Schema + Retry",
        "json_valid_rate": round(sum(x["json_valid"] for x in detailed) / n, 3),
        "pydantic_valid_rate": round(sum(x["pydantic_valid"] for x in detailed) / n, 3),
        "successful_results": sum(x["success"] for x in detailed),
        "total_retries": sum(x["retries"] for x in detailed),
        "mean_attempts": round(sum(x["attempts"] for x in detailed) / n, 3),
        "mean_time_s": round(sum(x["time_s"] for x in detailed) / n, 3),
        "total_tokens": sum(x["total_tokens"] or 0 for x in detailed),
        "mean_tokens_per_case": round(sum(x["total_tokens"] or 0 for x in detailed) / n, 3),
    }]
    return detailed, summary
