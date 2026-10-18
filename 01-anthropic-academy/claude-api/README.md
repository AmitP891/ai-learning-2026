# Claude API: multi-turn chat

My first script from **Building with the Claude API**, section 1 (Accessing Claude with the API).

## What it shows

- Calling the Messages API with the official Python SDK
- **Multi-turn conversations**: the API is stateless, so the script keeps a `messages` list and sends the full history every turn
- **System prompts**: setting Claude's role and style once, separate from the conversation
- **Temperature**: controlling how varied the responses are

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"   # from console.anthropic.com, never commit it
python chat.py
```

Type `quit` to exit.

## Next

The tool-use section extends this same loop so Claude can call Python functions.
