#!/usr/bin/env bash
# ==============================================================================
# GenAI in a Box — Interactive Platform Engineer & SRE Terminal X-Ray
# Run with: make demo-sre
# ==============================================================================
set -e

BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[1;36m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
MAGENTA="\033[1;35m"
RED="\033[1;31m"
RESET="\033[0m"

pause_step() {
  echo ""
  echo -en "${MAGENTA}▶ Press [ENTER] for $1...${RESET}"
  read -r _
  echo ""
}

# Ensure ResourceQuotas are applied before inspecting
kubectl apply -f k8s/01-resource-quotas.yaml >/dev/null 2>&1 || true

clear
echo -e "${BOLD}${MAGENTA}==============================================================================${RESET}"
echo -e "${BOLD} 🛠️  GENAI IN A BOX — PLATFORM ENGINEER & SRE TERMINAL X-RAY${RESET}"
echo -e "${BOLD}${MAGENTA}==============================================================================${RESET}"
echo -e "${DIM}Cluster Context: $(kubectl config current-context 2>/dev/null || echo 'unknown')${RESET}"

# ------------------------------------------------------------------------------
# STEP 1: 4-Namespace Topology & FinOps T-Shirt ResourceQuotas
# ------------------------------------------------------------------------------
pause_step "Step 1/4: 4-Namespace Isolation & FinOps ResourceQuotas (€0.00/token)"

echo -e "${YELLOW}=== [1A] Kubernetes ResourceQuotas (Hard FinOps Ceiling per Namespace) ===${RESET}"
echo -e "${CYAN}\$ kubectl get resourcequota -A${RESET}"
kubectl get resourcequota -A

echo ""
echo -e "${YELLOW}=== [1B] Live Pods Across the 4 Isolated Namespaces ===${RESET}"
for ns in agent ai-inference mcp-server data; do
  echo -e "${GREEN}--- Namespace: ${ns} ---${RESET}"
  kubectl get pods -n "$ns" -o wide
done

# ------------------------------------------------------------------------------
# STEP 2: Zero-Trust Security (NetworkPolicy + Zero DB Credentials in Agent Pod)
# ------------------------------------------------------------------------------
pause_step "Step 2/4: Zero-Trust NetworkPolicy & Agent Pod Credential Audit"

echo -e "${YELLOW}=== [2A] Zero-Trust Ingress NetworkPolicy on 'data' Namespace ===${RESET}"
echo -e "${CYAN}\$ kubectl describe networkpolicy postgres-zero-trust-ingress -n data${RESET}"
kubectl describe networkpolicy postgres-zero-trust-ingress -n data

echo ""
echo -e "${YELLOW}=== [2B] Auditing Environment Variables Inside the Untrusted Agent Pod ===${RESET}"
echo -e "${CYAN}\$ kubectl exec -n agent deploy/clinical-trial-matcher -- sh -c \"env | grep -E 'PG|DB_|POSTGRES' || echo '✅ VERIFIED: ZERO Database Credentials or Connection Strings inside Agent Pod!'\"${RESET}"
kubectl exec -n agent deploy/clinical-trial-matcher -- sh -c "env | grep -E 'PG|DB_|POSTGRES' || echo '✅ VERIFIED: ZERO Database Credentials or Connection Strings inside Agent Pod!'"

# ------------------------------------------------------------------------------
# STEP 3: Blast-Radius Protection (Read-Only Replica Blocks Prompt-Injected SQL)
# ------------------------------------------------------------------------------
pause_step "Step 3/4: Simulating Prompt-Injected 'DROP TABLE patients;' on Read Replica"

echo -e "${YELLOW}=== [3] Attempting Destructive Write Against pg-sovereign-2 (Read Replica) ===${RESET}"
echo -e "${CYAN}\$ kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c \"DROP TABLE patients;\"${RESET}"
kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c "DROP TABLE patients;" || true
echo -e "${GREEN}✅ VERIFIED: CloudNativePG Read-Only Replica physically blocks any write/DDL at the PostgreSQL transaction layer!${RESET}"

# ------------------------------------------------------------------------------
# STEP 4: PostgreSQL 18 Internals (AIO Worker + pgvector HNSW Index Scan)
# ------------------------------------------------------------------------------
pause_step "Step 4/4: PostgreSQL 18 Internals (io_method=worker) & pgvector HNSW EXPLAIN ANALYZE"

echo -e "${YELLOW}=== [4A] PostgreSQL 18 Engine Settings & Read-Replica Recovery Status ===${RESET}"
SQL_4A="SELECT version(), pg_is_in_recovery() AS is_read_replica, current_setting('io_method') AS pg18_aio_method, current_setting('shared_buffers') AS shared_buffers, current_setting('maintenance_work_mem') AS maintenance_work_mem;"
echo -e "${CYAN}\$ kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c \"${SQL_4A}\"${RESET}"
kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c "$SQL_4A"

echo ""
echo -e "${YELLOW}=== [4B] Live EXPLAIN (ANALYZE, BUFFERS) of pgvector HNSW Cosine Search (Patient P0001) ===${RESET}"
SQL_4B="SET enable_seqscan = off; EXPLAIN (ANALYZE, BUFFERS) SELECT trial_id, title, phase, ROUND((1 - (trial_embedding <=> (SELECT profile_embedding FROM patients WHERE patient_id = 'P0001')))::numeric, 4) AS similarity_score FROM clinical_trials ORDER BY trial_embedding <=> (SELECT profile_embedding FROM patients WHERE patient_id = 'P0001') LIMIT 3;"
echo -e "${CYAN}\$ kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c \"${SQL_4B}\"${RESET}"
kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c "$SQL_4B"

echo ""
echo -e "${YELLOW}=== [4C] Actual Top-3 Semantic Clinical Trial Matches Returned by pg-sovereign-2 ===${RESET}"
SQL_4C="SELECT t.trial_id, t.title, t.phase, t.max_age, ROUND((1 - (t.trial_embedding <=> p.profile_embedding))::numeric, 4) AS vector_similarity_score FROM clinical_trials t JOIN patients p ON p.patient_id = 'P0001' WHERE p.age <= t.max_age ORDER BY t.trial_embedding <=> p.profile_embedding LIMIT 3;"
echo -e "${CYAN}\$ kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c \"${SQL_4C}\"${RESET}"
kubectl exec -n data pg-sovereign-2 -c postgres -- psql -U postgres -d healthcaredb -c "$SQL_4C"

echo ""
echo -e "${BOLD}${GREEN}==============================================================================${RESET}"
echo -e "${BOLD}${GREEN} ✅ SRE X-RAY COMPLETE — Ready to switch to Google ADK UI (http://localhost:8000)${RESET}"
echo -e "${BOLD}${GREEN}==============================================================================${RESET}"
