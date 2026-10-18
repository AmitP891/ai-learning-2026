# Claude API: multi-turn chat

My first script from **Building with the Claude API**, section 1 (Accessing Claude with the API).

## What it shows

- Calling the Messages API with the official Python SDK
- **Multi-turn conversations**: the API is stateless, so the script keeps a `messages` list and sends the full history every turn
- **Content blocks**: Claude Sonnet 5.5 thinks by default, so a response can start with a `thinking` block. The script reads blocks by `type` instead of assuming `content[0]` is text
- **System prompts**: setting Claude's role and style once, separate from the conversation
- **Temperature (a lesson learned)**: the course covers it, but newer models such as Claude Sonnet 5.5 no longer accept custom `temperature`, `top_p` or `top_k` values, so this script leaves them out. See the [Sonnet 5.5 migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide).

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"   # from console.anthropic.com, never commit it
python chat.py
```

Type `quit` to exit.

## Next

The tool-use section extends this same loop so Claude can call Python functions.
