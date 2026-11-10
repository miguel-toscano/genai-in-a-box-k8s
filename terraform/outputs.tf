output "cluster_name" {
  description = "GKE Cluster Name"
  value       = google_container_cluster.sovereign_cluster.name
}

output "get_credentials_command" {
  description = "Command to configure kubectl credentials"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.sovereign_cluster.name} --region ${var.region} --project ${var.project_id}"
}

output "artifact_registry_url" {
  description = "Artifact Registry base URL for pushing images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.genai_repo.repository_id}"
}
