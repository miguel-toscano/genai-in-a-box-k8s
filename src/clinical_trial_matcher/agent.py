import logging
import os
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.toolbox_toolset import ToolboxToolset

logging.basicConfig(level=logging.INFO)

# In-cluster defaults (can be overridden locally when testing via kubectl port-forward)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama.ai-inference.svc.cluster.local:11434")
MCP_URL = os.environ.get("MCP_URL", "http://mcp-toolbox.mcp-server.svc.cluster.local:5000")
# Use ollama_chat/gemma4:e2b for native Ollama tool calling; swap to openai/gemma4:e2b when using vLLM
LLM_MODEL = os.environ.get("LLM_MODEL", "ollama_chat/gemma4:e2b")

os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_URL)

# 1. Connect to the governed MCP Toolbox for Databases (the only component with Postgres access)
toolbox = ToolboxToolset(
    server_url=MCP_URL,
    toolset_name="healthcare-toolset",
)

# 2. Sovereign Clinical Trial Matcher Agent powered by open-weights Gemma 4
root_agent = Agent(
    model=LiteLlm(
        model=LLM_MODEL,
        api_base=OLLAMA_URL,
    ),
    name="clinical_trial_matcher",
    description="Sovereign AI Clinical Trial Matcher running 100% air-gapped inside Kubernetes.",
    instruction="""You are an expert clinical research assistant running inside a sovereign, air-gapped Kubernetes cluster.
Your goal is to help doctors find patients with specific medical conditions, review their current treatments, and match them to eligible clinical trials using hybrid SQL + pgvector similarity search.

Always use the provided MCP tools to query patient records and clinical trials:
- `search_patients_by_condition`: Find patients diagnosed with a given condition (e.g., 'Diabetes', 'Asthma').
- `get_patient_profile`: Retrieve demographic details for a specific `patient_id`.
- `get_patient_conditions`: List all diagnoses for a `patient_id`.
- `get_patient_treatments`: List prescribed medications and dosages for a `patient_id`.
- `match_clinical_trials_for_patient`: Run a pgvector HNSW cosine similarity search (`<=>`) combined with age eligibility filters to find the top matching clinical trials for a `patient_id`.

Summarize your findings clearly with the patient ID, age, current medications, and the matched clinical trial IDs along with their vector similarity scores.""",
    tools=[toolbox],
)
