# AWS Observability, Drift Detection & Auto-Remediation Engine

> **Goal — Utilize AI Effectively for Engineering Productivity (Infra Project #1):** A self-healing infrastructure observability and Terraform configuration drift detection platform built with **Terraform**, **Prometheus**, **Grafana**, **Python FastAPI**, and **GitHub Actions** (`AWS Account: 160071257600 | ap-south-1`).

---

## 1. Why This Exists & What Problem It Solves

In production AWS environments, manual console edits frequently introduce out-of-band configuration drift (such as opening security groups to `0.0.0.0/0` or disabling storage encryption), while service degradations often go unnoticed until users report outages.

This platform solves both operational challenges:
* **Automated Terraform Drift Detection:** Continuously compares live environment attributes against the desired Infrastructure-as-Code baseline (`VPC CIDR`, `ECS desired count`, `RDS encryption`, `Security Group CIDRs`, and mandatory FinOps tags).
* **Self-Healing Auto-Remediation:** Exposes a reconciliation endpoint (`POST /api/drift/remediate`) that restores drifted attributes back to the Terraform baseline and resets alert gauges.
* **Real-Time Telemetry & SLO Dashboards:** Exports Prometheus metrics (`/metrics`) scraped every 5 seconds by **Prometheus** and visualized in **Grafana**.
* **Production AWS Cloud Guardrails (`infra/terraform/`):** Provisions multi-AZ VPC private subnets, Amazon ECS Fargate with Container Insights, immutable ECR repositories, Amazon SNS alert topics, CloudWatch CPU metric alarms, and hourly EventBridge drift-scan rules in AWS Account `160071257600`.

---

## 2. System Architecture

```mermaid
graph LR
    Engine[Drift & Telemetry Engine<br/>FastAPI :8080] -->|/metrics Scrape| Prom[Prometheus :9090]
    Prom -->|Query Metrics| Graf[Grafana Dashboards :3001]
    Engine -->|Detect Out-of-Band Drift| Diff[Terraform Baseline Comparator]
    Diff -->|Auto-Heal / Reconcile| Engine
    TF[Terraform IaC<br/>Account 160071257600] -->|Provisions| AWS[VPC + ECS Fargate +<br/>CloudWatch Alarms + SNS + EventBridge]