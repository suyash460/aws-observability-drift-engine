import copy
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(
    title="AWS Observability & Terraform Drift Remediation Engine",
    description="Prometheus metrics exporter, Terraform baseline drift detector, and automated self-healing controller.",
    version="1.0.0",
)

# Desired Infrastructure-as-Code Baseline (mirrors Terraform desired state)
DESIRED_STATE: Dict[str, Any] = {
    "vpc_cidr": "10.30.0.0/16",
    "ecs_desired_count": 2,
    "rds_storage_encrypted": True,
    "sg_ingress_cidrs": ["10.30.0.0/16"],
    "mandatory_tags": {"Environment": "production", "ManagedBy": "terraform", "Account": "160071257600"},
}

# Live simulated AWS environment state (can be mutated via /api/drift/simulate to test detection & healing)
LIVE_STATE: Dict[str, Any] = copy.deepcopy(DESIRED_STATE)

TELEMETRY = {
    "drift_checks_total": 0,
    "remediations_total": 0,
    "simulated_cpu_percent": 34.5,
    "simulated_http_5xx_rate": 0.0,
    "last_reconciled_at": datetime.now(timezone.utc).isoformat(),
}


class DriftMutation(BaseModel):
    sg_ingress_cidrs: List[str] = ["0.0.0.0/0"]
    ecs_desired_count: int = 1
    rds_storage_encrypted: bool = False


def compute_drift() -> List[Dict[str, Any]]:
    drifts = []
    for key, expected in DESIRED_STATE.items():
        actual = LIVE_STATE.get(key)
        if actual != expected:
            drifts.append({
                "attribute": key,
                "expected": expected,
                "actual": actual,
                "severity": "CRITICAL" if key in ("sg_ingress_cidrs", "rds_storage_encrypted") else "WARNING",
            })
    return drifts


@app.get("/health")
def health():
    return {"status": "healthy", "account_id": "160071257600", "region": "ap-south-1"}


@app.get("/api/drift/status")
def drift_status():
    TELEMETRY["drift_checks_total"] += 1
    drifts = compute_drift()
    return {
        "in_sync": len(drifts) == 0,
        "drift_count": len(drifts),
        "drifts": drifts,
        "last_reconciled_at": TELEMETRY["last_reconciled_at"],
    }


@app.post("/api/drift/simulate")
def simulate_drift(body: DriftMutation):
    LIVE_STATE["sg_ingress_cidrs"] = body.sg_ingress_cidrs
    LIVE_STATE["ecs_desired_count"] = body.ecs_desired_count
    LIVE_STATE["rds_storage_encrypted"] = body.rds_storage_encrypted
    TELEMETRY["simulated_cpu_percent"] = 88.2
    TELEMETRY["simulated_http_5xx_rate"] = 4.5
    return {"message": "Out-of-band AWS console drift simulated", "drifts": compute_drift()}


@app.post("/api/drift/remediate")
def remediate_drift():
    global LIVE_STATE
    drifts_before = compute_drift()
    if not drifts_before:
        return {"remediated": False, "message": "Infrastructure already in sync with Terraform baseline"}

    LIVE_STATE = copy.deepcopy(DESIRED_STATE)
    TELEMETRY["remediations_total"] += 1
    TELEMETRY["simulated_cpu_percent"] = 31.0
    TELEMETRY["simulated_http_5xx_rate"] = 0.0
    TELEMETRY["last_reconciled_at"] = datetime.now(timezone.utc).isoformat()
    return {
        "remediated": True,
        "repaired_attributes": [d["attribute"] for d in drifts_before],
        "in_sync": True,
        "last_reconciled_at": TELEMETRY["last_reconciled_at"],
    }


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    drifts = compute_drift()
    drift_flag = 1 if drifts else 0
    lines = [
        "# HELP aws_infra_drift_detected 1 if live AWS state diverges from Terraform baseline, 0 otherwise",
        "# TYPE aws_infra_drift_detected gauge",
        f"aws_infra_drift_detected {drift_flag}",
        "# HELP aws_infra_drift_items_count Number of drifted resource attributes",
        "# TYPE aws_infra_drift_items_count gauge",
        f"aws_infra_drift_items_count {len(drifts)}",
        "# HELP aws_infra_remediations_total Total automated drift remediations executed",
        "# TYPE aws_infra_remediations_total counter",
        f"aws_infra_remediations_total {TELEMETRY['remediations_total']}",
        "# HELP aws_ecs_cluster_cpu_utilization_percent Simulated ECS Fargate cluster CPU utilization",
        "# TYPE aws_ecs_cluster_cpu_utilization_percent gauge",
        f"aws_ecs_cluster_cpu_utilization_percent {TELEMETRY['simulated_cpu_percent']}",
        "# HELP aws_alb_http_5xx_rate_percent Simulated ALB HTTP 5xx error percentage",
        "# TYPE aws_alb_http_5xx_rate_percent gauge",
        f"aws_alb_http_5xx_rate_percent {TELEMETRY['simulated_http_5xx_rate']}",
    ]
    return "\n".join(lines) + "\n"