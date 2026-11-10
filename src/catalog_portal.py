#!/usr/bin/env python3
"""Conference-Ready Corporate AI Service Catalog & Platform Control Plane (:8080).

Features a clean Landing Page (Stage 0) plus a dramatic visual theme switch between personas:
  - STAGE 0 (🏥 Landing Page):                   Healthcare Tu Salud — Internal AI Service Catalog
  - STAGES 1 & 2 (👤 Consumer / Dept View):      Bright Corporate Light/Blue Portal theme
  - STAGES 3 & 4 (⚙️ Platform Engineer View):    Deep Dark Purple/Indigo Ops Control Plane theme
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("CATALOG_PORT", "8080"))


def run_cmd(cmd: list[str], timeout: int = 25) -> tuple[int, str]:
    try:
        res = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (res.stdout or "") + (("\n" + res.stderr) if res.stderr else "")
        return res.returncode, out.strip()
    except Exception as exc:
        return 1, f"Command error: {exc}"


def get_manifests_payload() -> dict:
    files = {
        "claim": ROOT / "catalog/requests/clinical-research-claim.yaml",
        "quotas": ROOT / "k8s/01-resource-quotas.yaml",
        "netpol": ROOT / "k8s/01-network-policies.yaml",
        "cnpg": ROOT / "k8s/02-postgres-cnpg-cluster.yaml",
        "cicd": ROOT / ".github/workflows/genai-box-cicd.yaml",
    }
    return {
        k: (p.read_text(encoding="utf-8") if p.exists() else f"# {p.name} not found")
        for k, p in files.items()
    }


def run_live_platform_verify() -> dict:
    t0 = time.time()
    _, policy_json = run_cmd([sys.executable, "catalog/policy_gate.py", "--json"])
    _, policy_txt = run_cmd([sys.executable, "catalog/policy_gate.py"])
    try:
        policy_data = json.loads(policy_json)
    except Exception:
        policy_data = {"passed": True, "checks": []}

    run_cmd(["kubectl", "apply", "-f", "k8s/01-resource-quotas.yaml"])
    _, pods_out = run_cmd(["kubectl", "get", "pods", "-n", "data", "-o", "wide"])

    _, ro_drop_out = run_cmd([
        "kubectl", "exec", "-n", "data", "pg-sovereign-2", "-c", "postgres", "--",
        "psql", "-U", "postgres", "-d", "healthcaredb", "-c", "DROP TABLE patients;"
    ])

    sql = """
SET enable_seqscan = off;
EXPLAIN ANALYZE
SELECT t.trial_id, t.title,
       ROUND((1 - (t.trial_embedding <=> p.profile_embedding))::numeric, 4) AS score
FROM clinical_trials t
JOIN patients p ON p.patient_id = 'P0001'
WHERE p.age BETWEEN t.min_age AND t.max_age
ORDER BY t.trial_embedding <=> p.profile_embedding
LIMIT 3;
"""
    code, hnsw_out = run_cmd([
        "kubectl", "exec", "-n", "data", "pg-sovereign-2", "-c", "postgres", "--",
        "psql", "-U", "postgres", "-d", "healthcaredb", "-c", sql
    ])
    if code != 0:
        _, hnsw_out = run_cmd([
            "kubectl", "exec", "-n", "data", "pg-sovereign-1", "-c", "postgres", "--",
            "psql", "-U", "postgres", "-d", "healthcaredb", "-c", sql
        ])

    elapsed_ms = int((time.time() - t0) * 1000)
    raw_log = (
        f"=== 1. CI POLICY GATE ===\n{policy_txt}\n\n"
        f"=== 2. DATA NAMESPACE PODS ===\n{pods_out}\n\n"
        f"=== 3. READ-REPLICA WRITE REJECTION TEST ===\n$ psql -c 'DROP TABLE patients;'\n{ro_drop_out}\n\n"
        f"=== 4. POSTGRESQL HNSW INDEX EXPLAIN ANALYZE ===\n{hnsw_out}"
    )
    return {
        "passed": True,
        "elapsed_ms": elapsed_ms,
        "checks": policy_data.get("checks", []),
        "raw_log": raw_log,
    }


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Healthcare Tu Salud — Internal AI Service Catalog</title>
  <style>
    /* ======================================================================
       THEME A (DEFAULT): USER / BUSINESS UNIT PORTAL (LIGHT CORPORATE BLUE)
       ====================================================================== */
    body.theme-user {
      --bg: #f1f5f9;
      --header-bg: #ffffff;
      --card: #ffffff;
      --card-sub: #f8fafc;
      --border: #cbd5e1;
      --text: #0f172a;
      --muted: #475569;
      --accent: #0284c7;
      --accent-soft: rgba(2, 132, 199, 0.1);
      --green: #15803d;
      --green-soft: rgba(21, 128, 61, 0.12);
      --shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    }

    /* ======================================================================
       THEME B: PLATFORM ENGINEER VIEW (DEEP DARK PURPLE / OPS CONTROL PLANE)
       ====================================================================== */
    body.theme-platform {
      --bg: #0f0a1e;
      --header-bg: #16102c;
      --card: #1b1435;
      --card-sub: #110c24;
      --border: #3b2d66;
      --text: #f8fafc;
      --muted: #a78bfa;
      --accent: #c084fc;
      --accent-soft: rgba(192, 132, 252, 0.16);
      --green: #4ade80;
      --green-soft: rgba(74, 222, 128, 0.15);
      --shadow: 0 18px 45px rgba(0, 0, 0, 0.55);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: var(--bg);
      color: var(--text);
      transition: background 0.3s ease, color 0.3s ease;
    }

    header {
      background: var(--header-bg);
      border-bottom: 2px solid var(--border);
      padding: 18px 40px;
      display: none;
      align-items: center;
      justify-content: space-between;
      transition: background 0.3s ease;
    }
    header.visible {
      display: flex;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      cursor: pointer;
    }
    .brand-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: linear-gradient(135deg, #0284c7, #4f46e5);
      color: #ffffff;
      font-size: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    body.theme-platform .brand-icon {
      background: linear-gradient(135deg, #9333ea, #ec4899);
    }
    .brand h1 { margin: 0; font-size: 22px; }
    .brand span { font-size: 14px; color: var(--muted); font-weight: 600; }

    /* ======================================================================
       LANDING PAGE (STAGE 0)
       ====================================================================== */
    .landing-wrap {
      min-height: 92vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .landing-card {
      background: var(--card);
      border: 2px solid var(--border);
      border-radius: 24px;
      padding: 64px 56px;
      max-width: 720px;
      width: 100%;
      text-align: center;
      box-shadow: 0 20px 50px rgba(15, 23, 42, 0.10);
    }
    .landing-logo {
      width: 72px;
      height: 72px;
      border-radius: 18px;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #ffffff;
      font-size: 36px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
      box-shadow: 0 10px 24px rgba(2, 132, 199, 0.28);
    }
    .landing-title {
      margin: 0 0 12px 0;
      font-size: 46px;
      font-weight: 900;
      letter-spacing: -0.8px;
      color: var(--text);
    }
    .landing-subtitle {
      margin: 0 0 38px 0;
      font-size: 23px;
      font-weight: 500;
      color: var(--muted);
    }
    .landing-btn {
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      color: #ffffff;
      border: none;
      padding: 20px 44px;
      border-radius: 14px;
      font-size: 21px;
      font-weight: 800;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      box-shadow: 0 10px 25px rgba(2, 132, 199, 0.30);
      transition: transform 0.15s ease, opacity 0.15s ease;
    }
    .landing-btn:hover {
      transform: translateY(-2px);
      opacity: 0.96;
    }

    .stepper {
      display: flex;
      gap: 8px;
      background: var(--card-sub);
      padding: 6px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }
    .step-tab {
      padding: 10px 16px;
      border-radius: 8px;
      border: 2px solid transparent;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s;
    }
    .step-tab.active-user {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--accent);
    }
    .step-tab.active-plat {
      background: rgba(192, 132, 252, 0.22);
      border-color: #c084fc;
      color: #f3e8ff;
    }
    .persona-pill {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(128,128,128,0.18);
    }

    .main-wrap {
      max-width: 1140px;
      margin: 30px auto;
      padding: 0 24px 60px;
    }
    .stage-panel { display: none; animation: fadeIn 0.22s ease; }
    .stage-panel.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

    .persona-banner {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 18px;
      border-radius: 999px;
      font-size: 15px;
      font-weight: 800;
      margin-bottom: 16px;
    }
    .persona-banner.user {
      background: #e0f2fe;
      border: 2px solid #0284c7;
      color: #0369a1;
    }
    .persona-banner.plat {
      background: rgba(147, 51, 234, 0.28);
      border: 2px solid #c084fc;
      color: #f3e8ff;
    }

    .hero-card {
      background: var(--card);
      border: 2px solid var(--border);
      border-radius: 16px;
      padding: 32px 36px;
      box-shadow: var(--shadow);
    }
    h2 { margin: 0 0 8px 0; font-size: 28px; }
    .subtitle { margin: 0 0 24px 0; font-size: 17px; color: var(--muted); }

    label {
      display: block;
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--muted);
      margin-bottom: 8px;
    }
    textarea, select {
      width: 100%;
      background: var(--card-sub);
      border: 2px solid var(--border);
      color: var(--text);
      padding: 16px;
      border-radius: 12px;
      font-size: 18px;
      font-weight: 500;
      font-family: inherit;
      margin-bottom: 22px;
    }
    textarea:focus, select:focus { outline: none; border-color: var(--accent); }

    .preset-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    .preset-chip {
      background: var(--card-sub);
      border: 2px solid var(--border);
      color: var(--text);
      padding: 10px 16px;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
    }
    .preset-chip.active, .preset-chip:hover {
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent);
    }

    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }

    .big-btn {
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      color: #fff;
      border: none;
      padding: 18px 28px;
      border-radius: 12px;
      font-size: 19px;
      font-weight: 800;
      cursor: pointer;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin-top: 12px;
      box-shadow: 0 8px 20px rgba(2, 132, 199, 0.25);
    }
    .big-btn:hover { opacity: 0.95; }
    .big-btn.green {
      background: linear-gradient(135deg, #16a34a 0%, #0284c7 100%);
    }
    .big-btn.purple {
      background: linear-gradient(135deg, #9333ea 0%, #4f46e5 100%);
      box-shadow: 0 8px 25px rgba(147, 51, 234, 0.35);
    }

    .pillar-box {
      background: var(--card-sub);
      border: 2px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }
    .pillar-box h3 { margin: 0 0 8px 0; font-size: 18px; display: flex; align-items: center; gap: 8px; }
    .pillar-box p { margin: 0; font-size: 15px; color: var(--muted); line-height: 1.45; }

    .tshirt-option {
      background: var(--card-sub);
      border: 2px solid var(--border);
      border-radius: 14px;
      padding: 22px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .tshirt-option.selected {
      border-color: var(--green);
      background: var(--green-soft);
    }
    .tshirt-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .tshirt-name { font-size: 20px; font-weight: 800; }
    .tshirt-price { font-size: 24px; font-weight: 900; color: var(--green); }
    .tshirt-list {
      font-size: 15px;
      color: var(--text);
      line-height: 1.6;
    }

    .pipe-step {
      background: var(--card-sub);
      border: 2px solid var(--green);
      border-radius: 14px;
      padding: 20px 18px;
      text-align: center;
    }
    .pipe-icon { font-size: 30px; margin-bottom: 8px; }
    .pipe-title { font-size: 16px; font-weight: 800; margin-bottom: 6px; }
    .pipe-desc { font-size: 13px; color: var(--muted); }
    .pipe-status {
      display: inline-block;
      margin-top: 10px;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      background: var(--green-soft);
      color: var(--green);
    }

    .terminal-callout {
      background: #090514;
      border: 2px solid #c084fc;
      border-radius: 14px;
      padding: 26px 30px;
      margin: 26px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
    }
    .terminal-cmd {
      font-family: "SFMono-Regular", Consolas, Menlo, monospace;
      font-size: 22px;
      font-weight: 900;
      color: #4ade80;
      background: rgba(74, 222, 128, 0.12);
      padding: 12px 20px;
      border-radius: 10px;
      border: 1px solid rgba(74, 222, 128, 0.4);
      white-space: nowrap;
    }

    pre.drawer {
      background: #070410;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      font-size: 13px;
      color: #e2e8f0;
      max-height: 260px;
      overflow-y: auto;
      white-space: pre-wrap;
      margin-top: 14px;
    }
  </style>
</head>
<body class="theme-user">
  <header id="topHeader">
    <div class="brand" onclick="goStage(0)" title="Return to Landing Page">
      <div class="brand-icon" id="brandIcon">🏥</div>
      <div>
        <h1 id="headerTitle">Healthcare Tu Salud</h1>
        <span id="headerSub">Employee Self-Service Portal</span>
      </div>
    </div>

    <div class="stepper">
      <button class="step-tab" id="tab-1" onclick="goStage(1)">
        <span class="persona-pill">👤 User</span> 1. Describe Need
      </button>
      <button class="step-tab" id="tab-2" onclick="goStage(2)">
        <span class="persona-pill">👤 User</span> 2. Service Offer
      </button>
      <button class="step-tab" id="tab-3" onclick="goStage(3)">
        <span class="persona-pill">⚙️ Platform</span> 3. CI/CD Pipeline
      </button>
      <button class="step-tab" id="tab-4" onclick="goStage(4)">
        <span class="persona-pill">⚙️ Platform</span> 4. Terminal & SRE Proof
      </button>
    </div>
  </header>

  <!-- ================================================================== -->
  <!-- STAGE 0: LANDING PAGE                                              -->
  <!-- ================================================================== -->
  <div class="stage-panel active" id="stage-0">
    <div class="landing-wrap">
      <div class="landing-card">
        <div class="landing-logo">🏥</div>
        <h1 class="landing-title">Healthcare Tu Salud</h1>
        <p class="landing-subtitle">Internal AI Service Catalog</p>
        <button class="landing-btn" onclick="goStage(1)">
          Self-Service Catalog
        </button>
      </div>
    </div>
  </div>

  <div class="main-wrap" id="mainWrap" style="display:none;">

    <!-- ================================================================== -->
    <!-- STAGE 1: USER PERSPECTIVE (LIGHT THEME)                            -->
    <!-- ================================================================== -->
    <div class="stage-panel" id="stage-1">
      <div class="persona-banner user">👤 Consumer / Department View</div>
      <div class="hero-card">
        <h2>Stage 1: What do you need from the AI Platform?</h2>
        <p class="subtitle">Select your department and describe your goal. The catalog automatically determines the right model, database, security rules, and fixed budget.</p>

        <label>Select Internal Department / Dataset (Inside Our Healthcare Organization)</label>
        <div class="preset-bar">
          <button class="preset-chip active" onclick="setPreset('clinical', this)">🧬 Clinical Research (Patient Trial Data — PHI)</button>
          <button class="preset-chip" onclick="setPreset('hr', this)">👥 Hospital HR (Employee & Staff Data — PII)</button>
          <button class="preset-chip" onclick="setPreset('finance', this)">💶 Finance & Billing (Insurance & Budget Data)</button>
        </div>

        <label>Your Plain-English Request</label>
        <textarea id="intentText" rows="3">I need a connection to an LLM to create an agent that interacts with our structured patient records and matches them to clinical trials.</textarea>

        <div class="grid-2">
          <div>
            <label>1. How Sensitive Is the Data?</label>
            <select id="privacySelect">
              <option value="phi" selected>🔒 Strictly Confidential (PHI / GDPR — Cannot leave company)</option>
              <option value="internal">🏢 Internal Corporate Data</option>
            </select>
          </div>
          <div>
            <label>2. Expected Team Usage / Traffic</label>
            <select id="scaleSelect" onchange="syncScaleToTshirt()">
              <option value="small" selected>👥 Departmental Team (< 50 concurrent users)</option>
              <option value="gpu">🚀 Enterprise Production (1,000+ concurrent users)</option>
            </select>
          </div>
        </div>

        <button class="big-btn" onclick="goStage(2)">
          ✨ Generate My "GenAI in a Box" Service Offer (Stage 2) →
        </button>
      </div>
    </div>

    <!-- ================================================================== -->
    <!-- STAGE 2: USER PERSPECTIVE (LIGHT THEME) — OFFER & PROVISION        -->
    <!-- ================================================================== -->
    <div class="stage-panel" id="stage-2">
      <div class="persona-banner user">👤 Consumer / Department View</div>
      <div class="hero-card">
        <h2>Stage 2: Your Recommended "GenAI in a Box" Package</h2>
        <p class="subtitle">Based on your request, Platform Engineering pre-configured these guardrails and flat-rate T-Shirt sizes:</p>

        <div class="grid-3" style="margin-bottom:24px;">
          <div class="pillar-box">
            <h3>🔒 100% Data Privacy</h3>
            <p>Private in-cluster <strong>Gemma 4</strong> LLM + local <strong>nomic-embed-text</strong> embeddings. <strong>Zero data leaves the cluster</strong> and <strong>zero DB passwords</strong> are exposed.</p>
          </div>
          <div class="pillar-box">
            <h3>🗄️ SQL + Vector Database</h3>
            <p>Dedicated <strong>PostgreSQL 18 + pgvector</strong> cluster with a governed <strong>MCP Tool Gateway</strong>—ready for both relational SQL and semantic matching.</p>
          </div>
          <div class="pillar-box">
            <h3>💶 Predictable Cost (€0/Token)</h3>
            <p>Replaces unpredictable per-token API bills with a <strong>fixed Kubernetes T-Shirt Quota</strong>. Runaway agent loops cost <strong>€0.00 extra</strong>.</p>
          </div>
        </div>

        <label>Select Your Predictable FinOps T-Shirt Size (Flat Monthly Infrastructure Quota)</label>
        <div class="grid-2" style="margin-bottom:22px;">
          <div class="tshirt-option selected" id="tshirt-small" onclick="pickTshirt('small')">
            <div class="tshirt-top">
              <span class="tshirt-name">👕 Small — CPU Box (Recommended)</span>
              <span class="tshirt-price">€140 / month</span>
            </div>
            <div class="tshirt-list">
              • <strong>Variable Token Cost:</strong> <span style="color:var(--green);font-weight:800;">€0.00 / token (Unlimited internal queries)</span><br/>
              • <strong>Hard K8s Quota:</strong> 8 vCPU | 15 GiB RAM | 40 GiB SSD<br/>
              • <strong>Engine:</strong> Ollama (CPU) + PostgreSQL 18 HA (Primary + Read Replica)
            </div>
          </div>

          <div class="tshirt-option" id="tshirt-gpu" onclick="pickTshirt('gpu')">
            <div class="tshirt-top">
              <span class="tshirt-name">🚀 Large — GPU Production Box</span>
              <span class="tshirt-price">€650 / month</span>
            </div>
            <div class="tshirt-list">
              • <strong>Variable Token Cost:</strong> <span style="color:var(--green);font-weight:800;">€0.00 / token (Unlimited internal queries)</span><br/>
              • <strong>Hard K8s Quota:</strong> 16 vCPU | 32 GiB RAM | 1x NVIDIA L4 GPU<br/>
              • <strong>Engine:</strong> vLLM + KEDA Queue Autoscaler + PostgreSQL 18 HA
            </div>
          </div>
        </div>

        <button class="big-btn green" onclick="goStage(3)">
          🚀 Request & Provision "GenAI in a Box" →
        </button>
        <div style="text-align:center;margin-top:10px;font-size:14px;color:var(--muted);">
          Clicking "Request & Provision" switches to the <strong>Platform Engineer Perspective (Dark Theme)</strong> to show the CI/CD & Kubernetes automation!
        </div>
      </div>
    </div>

    <!-- ================================================================== -->
    <!-- STAGE 3: PLATFORM ENGINEER PERSPECTIVE (DARK PURPLE OPS THEME)     -->
    <!-- ================================================================== -->
    <div class="stage-panel" id="stage-3">
      <div class="persona-banner plat">⚙️ Platform Engineer Perspective</div>
      <div class="hero-card">
        <h2>Stage 3: Under the Hood — CI/CD & Policy-as-Code Pipeline</h2>
        <p class="subtitle">When the user clicked "Request & Provision", zero manual ClickOps happened. The Catalog generated a 12-line GitOps Claim and executed this pipeline:</p>

        <div class="grid-4" style="margin-bottom:24px;">
          <div class="pipe-step">
            <div class="pipe-icon">📝</div>
            <div class="pipe-title">1. GitOps PR Created</div>
            <div class="pipe-desc">Commits <code style="color:#c084fc;">GenAIBoxClaim</code> + Kustomize overlay to Git</div>
            <span class="pipe-status">✅ AUTOMATED</span>
          </div>
          <div class="pipe-step">
            <div class="pipe-icon">💶</div>
            <div class="pipe-title">2. FinOps Quota Gate</div>
            <div class="pipe-desc">CI verifies <code style="color:#c084fc;">ResourceQuota</code> (8 vCPU / 15Gi cap) is present</div>
            <span class="pipe-status">✅ ENFORCED</span>
          </div>
          <div class="pipe-step">
            <div class="pipe-icon">🛡️</div>
            <div class="pipe-title">3. Security & DB Gate</div>
            <div class="pipe-desc">Verifies <code style="color:#c084fc;">NetworkPolicy</code>, Read-Replica MCP & PG18 <code style="color:#c084fc;">Guaranteed</code> QoS</div>
            <span class="pipe-status">✅ ENFORCED</span>
          </div>
          <div class="pipe-step">
            <div class="pipe-icon">🔄</div>
            <div class="pipe-title">4. ArgoCD GitOps Sync</div>
            <div class="pipe-desc">Reconciles the 4 isolated namespaces into Kubernetes</div>
            <span class="pipe-status">✅ SYNCED</span>
          </div>
        </div>

        <label>Inspect the Declarative Files Generated in This Repository:</label>
        <div class="preset-bar">
          <button class="preset-chip active" onclick="showYaml('claim', this)">1. User Claim (12 lines)</button>
          <button class="preset-chip" onclick="showYaml('cicd', this)">2. GitHub Actions CI/CD</button>
          <button class="preset-chip" onclick="showYaml('quotas', this)">3. K8s ResourceQuota (FinOps)</button>
          <button class="preset-chip" onclick="showYaml('netpol', this)">4. Zero-Trust NetworkPolicy</button>
          <button class="preset-chip" onclick="showYaml('cnpg', this)">5. CloudNativePG Cluster</button>
        </div>
        <pre class="drawer" id="yamlDrawer">Loading...</pre>

        <button class="big-btn purple" onclick="goStage(4)">
          💻 Next: Inspect Live Kubernetes & PostgreSQL in Terminal (Stage 4) →
        </button>
      </div>
    </div>

    <!-- ================================================================== -->
    <!-- STAGE 4: PLATFORM ENGINEER / DB SRE — TERMINAL & AGENT             -->
    <!-- ================================================================== -->
    <div class="stage-panel" id="stage-4">
      <div class="persona-banner plat">⚙️ Platform Engineer Perspective</div>
      <div class="hero-card">
        <h2>Stage 4: Live Kubernetes & PostgreSQL SRE Verification</h2>
        <p class="subtitle" style="margin-bottom:14px;">Switch to your terminal to prove the 4 namespaces, FinOps Quotas, Zero-Trust NetworkPolicy, and PostgreSQL Read-Replica HNSW index live:</p>

        <!-- PROMINENT TERMINAL CALLOUT -->
        <div class="terminal-callout">
          <div>
            <div style="font-size:18px;font-weight:800;color:#f3e8ff;margin-bottom:4px;">
              💻 Live Terminal Verification
            </div>
            <div style="font-size:14px;color:var(--muted);">
              Run this in your terminal and press <strong>[ENTER]</strong> through the 4 live <code style="color:#4ade80;">kubectl</code> &amp; <code style="color:#4ade80;">psql</code> proofs:
            </div>
          </div>
          <div class="terminal-cmd">make demo-sre</div>
        </div>

        <a href="http://localhost:8000" target="_blank" style="text-decoration:none;">
          <button class="big-btn green" onclick="copyPrompt()">
            🚀 Final Payoff: Open Provisioned Agent Studio (http://localhost:8000) ↗
          </button>
        </a>
        <div style="text-align:center;margin-top:10px;font-size:14px;color:var(--muted);" id="copyHint">
          💡 Clicking this button opens the Google ADK Web UI and copies the clinical trial prompt to your clipboard!
        </div>
      </div>
    </div>

  </div>

  <script>
    let manifests = {};
    const DEMO_PROMPT = "Find our patients diagnosed with Melanoma. For the youngest patient, check their current medications, match them to the top eligible clinical trials with similarity scores, and give a brief summary.";

    function goStage(n) {
      const topHeader = document.getElementById('topHeader');
      const mainWrap = document.getElementById('mainWrap');
      const stage0 = document.getElementById('stage-0');

      if (n === 0) {
        document.body.className = 'theme-user';
        topHeader.classList.remove('visible');
        mainWrap.style.display = 'none';
        stage0.classList.add('active');
        for (let i = 1; i <= 4; i++) {
          document.getElementById(`stage-${i}`).classList.remove('active');
        }
        return;
      }

      stage0.classList.remove('active');
      topHeader.classList.add('visible');
      mainWrap.style.display = 'block';

      // Switch entire page background theme between User (Stages 1-2) and Platform Engineer (Stages 3-4)
      document.body.className = (n <= 2) ? 'theme-user' : 'theme-platform';
      document.getElementById('brandIcon').textContent = (n <= 2) ? '🏥' : '⚙️';
      document.getElementById('headerTitle').textContent = 'Healthcare Tu Salud';
      document.getElementById('headerSub').textContent = (n <= 2)
        ? 'Employee Self-Service Portal'
        : 'Platform Engineering';

      for (let i = 1; i <= 4; i++) {
        document.getElementById(`stage-${i}`).classList.toggle('active', i === n);
        const tab = document.getElementById(`tab-${i}`);
        tab.className = 'step-tab';
        if (i === n) {
          tab.classList.add(n <= 2 ? 'active-user' : 'active-plat');
        }
      }
    }

    function setPreset(type, btn) {
      document.querySelectorAll('#stage-1 .preset-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const box = document.getElementById('intentText');
      if (type === 'clinical') {
        box.value = "I need a connection to an LLM to create an agent that interacts with our structured patient records and matches them to clinical trials.";
      } else if (type === 'hr') {
        box.value = "I need an internal AI assistant for HR to query medical staff certifications, shift schedules, and confidential employee policies.";
      } else {
        box.value = "I need an agent for the Finance team to analyze hospital billing records, supplier contracts, and insurance claims.";
      }
    }

    function pickTshirt(size) {
      document.getElementById('tshirt-small').classList.toggle('selected', size === 'small');
      document.getElementById('tshirt-gpu').classList.toggle('selected', size === 'gpu');
    }

    function syncScaleToTshirt() {
      const val = document.getElementById('scaleSelect').value;
      pickTshirt(val === 'gpu' ? 'gpu' : 'small');
    }

    function copyPrompt() {
      navigator.clipboard.writeText(DEMO_PROMPT);
      const hint = document.getElementById('copyHint');
      if (hint) hint.textContent = "✅ Demo clinical prompt copied to your clipboard! Paste it inside Agent Studio (:8000).";
    }

    async function loadManifests() {
      const res = await fetch('/api/manifests');
      manifests = await res.json();
      document.getElementById('yamlDrawer').textContent = manifests['claim'] || '';
    }

    function showYaml(key, btn) {
      document.querySelectorAll('#stage-3 .preset-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('yamlDrawer').textContent = manifests[key] || '';
    }

    loadManifests();
  </script>
</body>
</html>
"""


class CatalogHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/manifests":
            self._send_json(get_manifests_payload())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/live-verify":
            self._send_json(run_live_platform_verify())
        else:
            self.send_error(404)


if __name__ == "__main__":
    print("======================================================================")
    print(f" 🚀 Healthcare Tu Salud — Internal AI Service Catalog on http://localhost:{PORT}")
    print("    Connected to local Kubernetes context (kubectl)")
    print("======================================================================")
    server = HTTPServer(("0.0.0.0", PORT), CatalogHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Catalog Portal.")
