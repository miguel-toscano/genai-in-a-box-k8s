# Sovereign AI GKE Cluster (Private Nodes + Shielded Secure Boot for Argolis compliance)
resource "google_container_cluster" "sovereign_cluster" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # Manage node pool separately for clean lifecycle
  remove_default_node_pool = true
  initial_node_count       = 1

  # VPC-native (Alias IP) networking
  ip_allocation_policy {}

  # Private nodes (zero public IPs on worker VMs) with public control-plane endpoint for Cloud Shell access
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.authorized_ipv4_cidr
      display_name = "authorized-operator-ip"
    }
  }

  # Shielded Nodes required by Argolis org policies
  enable_shielded_nodes = true

  deletion_protection = false

  depends_on = [
    google_compute_subnetwork.subnet,
    google_compute_router_nat.nat,
  ]
}

resource "google_container_node_pool" "primary_cpu_nodes" {
  name       = "sovereign-cpu-pool"
  location   = var.region
  cluster    = google_container_cluster.sovereign_cluster.name
  node_count = var.node_count # 1 per zone in regional cluster = 3 nodes total (e2-standard-4)

  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-balanced"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    labels = {
      workload-tier = "sovereign-ai-box"
    }
  }
}
