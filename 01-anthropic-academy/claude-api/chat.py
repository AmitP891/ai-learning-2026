"""Multi-turn chat with Claude: Anthropic Academy, Building with the Claude API, section 1."""
import anthropic

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
        max_tokens=500,
        system=SYSTEM,
        temperature=0.7,
        messages=messages,
    )
    reply = response.content[0].text
    messages.append({"role": "assistant", "content": reply})
    print(f"\nClaude: {reply}\n")
