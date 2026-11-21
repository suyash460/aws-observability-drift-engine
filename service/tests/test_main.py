from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_and_initial_in_sync_state():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["account_id"] == "160071257600"

    status = client.get("/api/drift/status").json()
    assert status["in_sync"] is True
    assert status["drift_count"] == 0


def test_drift_simulation_metrics_and_auto_remediation():
    sim = client.post(
        "/api/drift/simulate",
        json={"sg_ingress_cidrs": ["0.0.0.0/0"], "ecs_desired_count": 1, "rds_storage_encrypted": False},
    )
    assert sim.status_code == 200
    assert len(sim.json()["drifts"]) == 3

    metrics_text = client.get("/metrics").text
    assert "aws_infra_drift_detected 1" in metrics_text
    assert "aws_infra_drift_items_count 3" in metrics_text

    heal = client.post("/api/drift/remediate").json()
    assert heal["remediated"] is True
    assert heal["in_sync"] is True

    metrics_after = client.get("/metrics").text
    assert "aws_infra_drift_detected 0" in metrics_after