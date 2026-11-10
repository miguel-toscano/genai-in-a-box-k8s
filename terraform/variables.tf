variable "project_id" {
  description = "The GCP Project ID (e.g. your-gcp-project-id)"
  type        = string
  default     = "your-gcp-project-id"
}

variable "region" {
  description = "GCP region for the VPC and GKE cluster"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name of the Sovereign AI GKE cluster"
  type        = string
  default     = "sovereign-ai-cluster"
}

variable "network_name" {
  description = "Name of the custom VPC network"
  type        = string
  default     = "sovereign-ai-net"
}

variable "subnet_name" {
  description = "Name of the private subnet"
  type        = string
  default     = "sovereign-ai-subnet"
}

variable "subnet_cidr" {
  description = "CIDR range for the primary GKE subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for the GKE private master control plane"
  type        = string
  default     = "172.16.0.0/28"
}

variable "node_machine_type" {
  description = "Machine type for the CPU node pool (runs Postgres + pgvector, Ollama gemma4:e2b, MCP Toolbox, and ADK)"
  type        = string
  default     = "e2-standard-4"
}

variable "node_count" {
  description = "Number of nodes per zone (or total in regional/zonal cluster)"
  type        = number
  default     = 1
}

variable "authorized_ipv4_cidr" {
  description = "Authorized CIDR block (e.g. your Cloud Shell / workstation IP /32) allowed to reach the GKE public control plane endpoint"
  type        = string
  default     = "0.0.0.0/0"
}
