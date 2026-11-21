output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "sns_alerts_topic_arn" {
  value = aws_sns_topic.infra_alerts.arn
}

output "ecr_repository_url" {
  value = aws_ecr_repository.drift_engine.repository_url
}