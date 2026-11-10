resource "google_artifact_registry_repository" "genai_repo" {
  location      = var.region
  repository_id = "genai-box-repo"
  description   = "Internal container registry for GenAI in a Box workloads (ADK Agent & tools)"
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [google_project_service.required_apis]
}

data "google_project" "current" {
  project_id = var.project_id
  depends_on = [google_project_service.required_apis]
}

# Allow GKE nodes to pull private images from Artifact Registry
resource "google_project_iam_member" "gke_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}
