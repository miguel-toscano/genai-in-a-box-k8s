PROJECT_ID       ?= your-gcp-project-id
REGION           ?= us-central1
CLUSTER          ?= sovereign-ai-cluster
KIND_CLUSTER     ?= genai-box
REPO             ?= genai-box-repo
IMAGE_TAG        ?= latest
LOCAL_IMAGE      ?= localhost/genai-box/agent:$(IMAGE_TAG)
CNPG_VER         ?= 1.28.0
CONTAINER_ENGINE ?= $(shell command -v docker >/dev/null 2>&1 && echo docker || echo podman)

export KIND_EXPERIMENTAL_PROVIDER=$(CONTAINER_ENGINE)

.PHONY: help local-podman-init local-cluster local-build-agent local-deploy-box local-all \
        tf-init tf-apply get-credentials install-cnpg generate-data build-agent deploy-box \
        status port-forward catalog-ui ci-policy-check demo demo-sre

help:
	@echo "======================================================================"
	@echo " GenAI in a Box: Sovereign AI Platform on Kubernetes                  "
	@echo "======================================================================"
	@echo "Local Laptop Targets (Podman/Docker + Kind, Minikube, Rancher Desktop):"
	@echo "  make local-podman-init  Initialize & start a rootful Podman Machine (6 CPUs, 12GB RAM)"
	@echo "  make local-cluster      Create local Kind cluster ($(CONTAINER_ENGINE)) & install CloudNativePG $(CNPG_VER)"
	@echo "  make local-build-agent  Build ADK Agent with $(CONTAINER_ENGINE) & load archive into Kind"
	@echo "  make local-deploy-box   Deploy the 4-namespace Sovereign GenAI Box to active kubectl context"
	@echo "  make local-all          Run local-cluster + local-build-agent + local-deploy-box"
	@echo "  (Tip: Pass CONTAINER_ENGINE=docker to use Docker instead of Podman)"
	@echo ""
	@echo "Platform Engineering & Live Demo Targets:"
	@echo "  make demo               Launch BOTH the Service Catalog Portal (:8080) & ADK Agent (:8000)"
	@echo "  make demo-sre           Interactive 4-step Platform Engineer / SRE live cluster X-Ray"
	@echo "  make catalog-ui         Launch the Corporate AI Service Catalog & CI/CD Portal on :8080"
	@echo "  make ci-policy-check    Run the CI/CD Policy-as-Code Gate linter (catalog/policy_gate.py)"
	@echo "  make status             Check status of all 4 namespaces (data, ai-inference, mcp-server, agent)"
	@echo "  make port-forward       Port-forward ADK Web UI (:8000) to http://localhost:8000"
	@echo ""
	@echo "Cloud Targets (GKE + Terraform):"
	@echo "  make tf-init            Initialize Terraform in ./terraform"
	@echo "  make tf-apply           Provision VPC, Cloud NAT, Artifact Registry & GKE in $(PROJECT_ID)"
	@echo "  make get-credentials    Configure kubectl for $(CLUSTER) and authorize current IP"
	@echo "  make install-cnpg       Install open-source CloudNativePG $(CNPG_VER) (supports PG18)"
	@echo "  make build-agent        Build & push ADK Agent container to GCP Artifact Registry"
	@echo "  make deploy-box         Deploy the 4-namespace Sovereign GenAI Box to GKE"

# ---------------------------------------------------------------------------
# 1. Local Deployment Workflow (Podman or Docker + Kind / Local Kubernetes)
# ---------------------------------------------------------------------------
local-podman-init:
	mkdir -p ~/.config/containers
	@grep -q 'provider = "applehv"' ~/.config/containers/containers.conf 2>/dev/null || printf "[machine]\nprovider = \"applehv\"\n" >> ~/.config/containers/containers.conf
	CONTAINERS_MACHINE_PROVIDER=applehv podman machine init --rootful --cpus 6 --memory 12288 --disk-size 60 || true
	CONTAINERS_MACHINE_PROVIDER=applehv podman machine set --rootful --cpus 6 --memory 12288
	CONTAINERS_MACHINE_PROVIDER=applehv podman machine start

local-cluster:
	KIND_EXPERIMENTAL_PROVIDER=$(CONTAINER_ENGINE) kind create cluster --name $(KIND_CLUSTER)
	$(MAKE) install-cnpg

local-build-agent:
	$(CONTAINER_ENGINE) build -f src/Dockerfile.agent -t $(LOCAL_IMAGE) .
	rm -f /tmp/genai-agent.tar
	$(CONTAINER_ENGINE) save $(LOCAL_IMAGE) -o /tmp/genai-agent.tar
	KIND_EXPERIMENTAL_PROVIDER=$(CONTAINER_ENGINE) kind load image-archive /tmp/genai-agent.tar --name $(KIND_CLUSTER)
	rm -f /tmp/genai-agent.tar

local-deploy-box: generate-data
	kubectl apply -f k8s/00-namespaces.yaml
	kubectl apply -f k8s/01-network-policies.yaml
	kubectl apply -f k8s/01-resource-quotas.yaml
	kubectl apply -f k8s/04-ollama-inference.yaml
	kubectl create configmap clinical-data --from-file=data/ -n data --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/02-postgres-cnpg-cluster.yaml
	@echo "Waiting for CloudNativePG PostgreSQL 18 cluster 'pg-sovereign' to become Ready..."
	kubectl wait --for=condition=Ready cluster/pg-sovereign -n data --timeout=300s
	kubectl delete job data-loader -n data --ignore-not-found
	kubectl apply -f k8s/03-data-hydration-job.yaml
	kubectl apply -f k8s/05-mcp-toolbox.yaml
	kubectl apply -f k8s/06-adk-agent.yaml

local-all: local-cluster local-build-agent local-deploy-box

# ---------------------------------------------------------------------------
# 2. Cloud Deployment Workflow (GKE + Terraform)
# ---------------------------------------------------------------------------
tf-init:
	cd terraform && terraform init

tf-apply:
	cd terraform && terraform apply -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)"

get-credentials:
	gcloud container clusters get-credentials $(CLUSTER) --region $(REGION) --project $(PROJECT_ID)
	@MY_IP=$$(curl -s ifconfig.me); \
	echo "Authorizing IP $$MY_IP/32 on GKE master..."; \
	gcloud container clusters update $(CLUSTER) \
		--region $(REGION) \
		--project $(PROJECT_ID) \
		--enable-master-authorized-networks \
		--master-authorized-networks="$$MY_IP/32"

install-cnpg:
	kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.28/releases/cnpg-$(CNPG_VER).yaml
	kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=180s

generate-data:
	python3 src/generate_data.py

build-agent:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev --quiet
	$(CONTAINER_ENGINE) build -f src/Dockerfile.agent -t $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/agent:$(IMAGE_TAG) .
	$(CONTAINER_ENGINE) push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/agent:$(IMAGE_TAG)

deploy-box: generate-data
	kubectl apply -f k8s/00-namespaces.yaml
	kubectl apply -f k8s/01-network-policies.yaml
	kubectl apply -f k8s/01-resource-quotas.yaml
	kubectl apply -f k8s/04-ollama-inference.yaml
	kubectl create configmap clinical-data --from-file=data/ -n data --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/02-postgres-cnpg-cluster.yaml
	@echo "Waiting for CloudNativePG PostgreSQL 18 cluster 'pg-sovereign' to become Ready..."
	kubectl wait --for=condition=Ready cluster/pg-sovereign -n data --timeout=300s
	kubectl delete job data-loader -n data --ignore-not-found
	kubectl apply -f k8s/03-data-hydration-job.yaml
	kubectl apply -f k8s/05-mcp-toolbox.yaml
	sed "s|localhost/genai-box/agent:latest|$(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/agent:$(IMAGE_TAG)|g" k8s/06-adk-agent.yaml | kubectl apply -f -

status:
	@echo "=== CloudNativePG PostgreSQL 18 Cluster (namespace: data) ==="
	kubectl get cluster,pods,pvc -n data
	@echo "\n=== AI Inference & Embeddings (namespace: ai-inference) ==="
	kubectl get pods,pvc,svc -n ai-inference
	@echo "\n=== MCP Toolbox Gateway (namespace: mcp-server) ==="
	kubectl get pods,svc -n mcp-server
	@echo "\n=== Google ADK Agent (namespace: agent) ==="
	kubectl get pods,svc -n agent

port-forward:
	@echo "Opening ADK Web UI on http://localhost:8000 ..."
	kubectl port-forward svc/clinical-trial-matcher -n agent 8000:8000

ci-policy-check:
	python3 catalog/policy_gate.py

catalog-ui:
	kubectl apply -f k8s/01-resource-quotas.yaml >/dev/null 2>&1 || true
	python3 src/catalog_portal.py

demo:
	kubectl apply -f k8s/01-resource-quotas.yaml >/dev/null 2>&1 || true
	@echo "======================================================================"
	@echo " 1. Corporate AI Service Catalog & CI/CD Portal -> http://localhost:8080"
	@echo " 2. Google ADK Sovereign Agent Studio           -> http://localhost:8000"
	@echo " 3. In a second terminal tab, run:              make demo-sre"
	@echo "======================================================================"
	@kubectl port-forward svc/clinical-trial-matcher -n agent 8000:8000 >/dev/null 2>&1 & \
	PF_PID=$$!; \
	trap "kill $$PF_PID 2>/dev/null || true" EXIT INT TERM; \
	python3 src/catalog_portal.py

demo-sre:
	@bash src/demo_sre.sh
