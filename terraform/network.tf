# Enable required Google Cloud APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Custom VPC Network (Argolis Org Policy compliant: no default network)
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false
  project                 = var.project_id

  depends_on = [google_project_service.required_apis]
}

# Private Subnet with Private Google Access enabled
resource "google_compute_subnetwork" "subnet" {
  name                     = var.subnet_name
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

# Cloud Router & Cloud NAT (Allows private nodes to pull initial container images / helm charts without external Node IPs)
resource "google_compute_router" "router" {
  name    = "${var.network_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.network_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Allow GKE Control Plane to reach admission webhooks (e.g. CloudNativePG operator webhook on port 9443)
resource "google_compute_firewall" "allow_master_webhooks" {
  name        = "allow-gke-master-webhooks"
  network     = google_compute_network.vpc.name
  description = "Allow GKE control plane to reach operator admission webhooks (port 9443/8443)"

  allow {
    protocol = "tcp"
    ports    = ["8443", "9443"]
  }

  source_ranges = [var.master_ipv4_cidr_block]
}
