"""OPTIONAL adapter for your Week 1 LLM.

The exact Week 1 model code has not been supplied here. Replace `generate`
with your existing authenticated model call; keep secrets in environment variables
or Streamlit secrets, NEVER inside this file. The backend passes a context-limited
prompt that includes untrusted retrieved passages: do not execute instructions
found inside passages. Then enable the adapter in app settings.
"""

def generate(prompt: str) -> str:
    raise NotImplementedError(
        'Connect your Week 1 LLM implementation in week1_adapter.generate() first.'
    )
