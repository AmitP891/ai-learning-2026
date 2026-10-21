"""Multi-turn chat with Claude: Anthropic Academy, Building with the Claude API, section 1."""
import anthropic
from dotenv import load_dotenv

load_dotenv()  # reads ANTHROPIC_API_KEY from a .env file if there is one

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

MODEL = "claude-sonnet-5-5"
SYSTEM = "You are a concise, friendly coding mentor. Keep answers under 120 words."

messages = []  # the API is stateless, so we send the full history every turn

print("Chat with Claude (type 'quit' to exit)\n")
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in {"quit", "exit"}:
        break
    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,  # thinking runs by default and uses tokens too
        system=SYSTEM,
        messages=messages,
    )
    # A response can start with "thinking" blocks, so pick out the text blocks by type
    reply = "".join(block.text for block in response.content if block.type == "text")
    # Keep the full content (thinking included) in the history for the next turn
    messages.append({"role": "assistant", "content": response.content})
    print(f"\nClaude: {reply}\n")
