"""
chatbot/agent.py

A small LangGraph ReAct-style agent: the LLM can call FinPulse's own
DB-query tools (chatbot/tools.py) to answer questions about tracked
stocks, then must respond briefly (enforced via system prompt).

Uses Anthropic's Claude via langchain_anthropic. Set ANTHROPIC_API_KEY
in your environment / .env file.
"""

import os
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from chatbot.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are FinPulse Assistant, a concise financial data assistant.

Rules:
- Answer ONLY using the tools provided (they query FinPulse's own database of tracked stocks).
- Keep every answer to 2-3 short sentences maximum. No long explanations, no disclaimers, no filler.
- If a ticker isn't tracked or has no data, say so in one sentence.
- Never give investment advice or recommendations to buy/sell — only report the data.
- Use plain numbers with ₹ for currency, no markdown tables.
"""

_model = ChatAnthropic(
    model=os.getenv("CHATBOT_MODEL", "claude-sonnet-4-6"),
    temperature=0,
    max_tokens=200,  # hard cap to keep responses short
)

# langgraph 0.2.62 takes `state_modifier`; the `prompt=` kwarg only exists in 0.3+.
agent = create_react_agent(_model, ALL_TOOLS, state_modifier=SYSTEM_PROMPT)


def ask_finpulse_bot(question: str) -> str:
    """Run the agent on a single question and return the final text answer."""
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    final_message = result["messages"][-1]
    return final_message.content


if __name__ == "__main__":
    print(ask_finpulse_bot("What's the P/E ratio of RELIANCE?"))
