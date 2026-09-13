# Copilot Chat Client

Minimal Python stdlib client สำหรับเชื่อม Enterprise Copilot Chat gateway

## Environment

```bash
export RESEARCH_OS_COPILOT_API_URL="https://enterprise-gateway.example.com/copilot/chat"
export RESEARCH_OS_COPILOT_API_KEY="..."
export RESEARCH_OS_COPILOT_MODEL="copilot-enterprise"
```

## Example

```python
from tools.copilot_chat import CopilotChatClient

client = CopilotChatClient()
result = client.chat(
    messages=[{"role": "user", "content": "Summarize this repository"}],
    context={"repository": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"},
)
print(result["reply"])
```
