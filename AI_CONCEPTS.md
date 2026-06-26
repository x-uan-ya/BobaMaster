```python
import asyncio
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


# Background:
# This agent is designed for Montimage to enhance threat intelligence
# capabilities using the MITRE ATT&CK framework.


async def initialize_advanced_agent():
    """
    Sets up the MITRE-MCP client, loads security tools,
    and initializes the LangChain agent.
    """

    # 1. Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key="YOUR_OPENAI_API_KEY"
    )

    # 2. Connect to the MITRE-MCP Server
    mitre_attack_client = MultiServerMCPClient(
        {
            "mitreattack": {
                "transport": "http",
                "url": "http://localhost:8088/mcp",
            }
        }
    )

    # 3. Load MCP Tools
    mitre_tools = await mitre_attack_client.get_tools()

    # 4. Define Toolset
    agent_tools = mitre_tools

    # 5. Create the Agent
    agent = create_agent(
        llm,
        agent_tools
    )

    return agent


async def main():
    # Setup the agent
    security_agent = await initialize_advanced_agent()

    # Example usage
    response = await security_agent.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content="What sub-techniques are associated with phishing (T1566) in MITRE ATT&CK?"
                )
            ]
        }
    )

    print(response)


if __name__ == "__main__":
    asyncio.run(main())
```
