# -----------------------------
# Artifact Registry
# -----------------------------
resource "google_artifact_registry_repository" "gateway" {
  location      = var.region
  repository_id = "ai-gateway"
  format        = "DOCKER"
}

# -----------------------------
# Runtime Service Account
# -----------------------------
resource "google_service_account" "gateway_runtime" {
  account_id   = "gateway-runtime-sa"
  display_name = "AI Gateway Runtime Service Account"
}

# -----------------------------
# Secret Manager
# -----------------------------
resource "google_secret_manager_secret" "model_api_key" {
  secret_id = "model-api-key"

  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "model_api_key_v1" {
  secret      = google_secret_manager_secret.model_api_key.id
  secret_data = "placeholder-change-me"
}

# -----------------------------
# IAM - allow service to read secret
# -----------------------------
resource "google_secret_manager_secret_iam_member" "gateway_secret_access" {
  secret_id = google_secret_manager_secret.model_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_runtime.email}"
}

# -----------------------------
# Cloud Run Service (placeholder)
# -----------------------------
resource "google_cloud_run_v2_service" "gateway" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.gateway_runtime.email

    containers {
      image = "us-central1-docker.pkg.dev/silver-origin-161220/ai-gateway/gateway:v6"

      env {
        name = "MODEL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.model_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "DEFAULT_PROVIDER"
        value = "openai"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = "silver-origin-161220"
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

# -----------------------------
# Public access (DEBUG / DEMO ONLY)
# -----------------------------
# WARNING: Enables unauthenticated access to the service.
# Do NOT enable in production environments.
#
# resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
#   project  = google_cloud_run_v2_service.gateway.project
#   location = google_cloud_run_v2_service.gateway.location
#   name     = google_cloud_run_v2_service.gateway.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }