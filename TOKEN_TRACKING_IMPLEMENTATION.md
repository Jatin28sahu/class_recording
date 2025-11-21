# Token Tracking Implementation with LangChain & LangSmith

## Overview
This document explains the token tracking implementation for the class recording project. The solution uses **LangChain's built-in integrations** which automatically handle token tracking and reporting to LangSmith, eliminating the need for manual token extraction.

## What Was Changed

### 1. Dependencies Updated (`requirements.txt`)
Added the following packages:
- `langsmith>=0.1.0` - LangSmith SDK for observability
- `langgraph>=0.2.0` - LangGraph for workflow orchestration  
- `langchain>=0.3.0` - Core LangChain library
- `langchain-openai>=0.2.0` - OpenAI integration with automatic token tracking
- `langchain-google-genai>=2.0.0` - Google Gemini integration with automatic token tracking

### 2. Files Modified
- `class_test_graph.py` - Updated to use LangChain's ChatOpenAI and ChatGoogleGenerativeAI
- `class_tutor_graph.py` - Updated to use LangChain's ChatOpenAI

## How It Works

### Automatic Token Tracking
LangChain's model integrations automatically:
1. **Capture token usage** from API responses (input tokens, output tokens, total tokens)
2. **Track detailed breakdowns** (cached tokens, reasoning tokens, audio tokens, etc.)
3. **Calculate costs** based on model pricing in LangSmith
4. **Send data to LangSmith** when tracing is enabled

### Before (Manual Extraction)
```python
from openai import OpenAI

client = OpenAI(api_key=api_key)
resp = client.chat.completions.create(...)

# Manual extraction required
if resp.usage:
    usage_metadata = {
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
        # ... more manual extraction
    }
    run = get_current_run_tree()
    run.set(usage_metadata=usage_metadata)
```

### After (Automatic with LangChain)
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatOpenAI(model=model, temperature=0.3, api_key=api_key)
messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

# Token tracking happens automatically!
response = llm.invoke(messages)
```

## Environment Configuration

Make sure these environment variables are set in your `.env` file:
```bash
# Required: At least one LLM provider
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key  # Optional

# Required: LangSmith configuration
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT="SMART_CLASS_NOTES"
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## Viewing Token Usage

### 1. LangSmith UI (https://smith.langchain.com)
- **Trace Tree View**: See token usage for each individual LLM call
- **Project Stats**: View aggregated token usage and costs for all traces
- **Dashboards**: Create custom charts to track token usage trends over time
- **Cost Breakdowns**: Hover over cost sections to see detailed breakdowns by token type

### 2. Token Information Available
- Input tokens (prompt tokens)
- Output tokens (completion tokens)
- Total tokens
- Cached tokens (for models with caching)
- Reasoning tokens (for models like o1)
- Audio/Image tokens (for multimodal models)
- Estimated costs (based on model pricing)

## Benefits of This Approach

1. **No Manual Code**: No need to extract and format token data manually
2. **Automatic Updates**: When OpenAI/Gemini add new token types, LangChain handles them
3. **Built-in Cost Tracking**: Costs are automatically calculated based on model pricing
4. **Consistent Format**: All token data follows LangSmith's standard format
5. **Detailed Breakdowns**: Automatically captures specialized token types (cache, reasoning, etc.)
6. **Multi-Provider Support**: Works seamlessly with OpenAI, Gemini, and other providers

## Testing Token Tracking

To verify token tracking is working:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** in `.env` (see above)

3. **Run the pipeline**:
   ```bash
   python class_test_graph.py
   # or
   python class_tutor_graph.py
   ```

4. **Check LangSmith**:
   - Go to https://smith.langchain.com
   - Navigate to your project: "SMART_CLASS_NOTES"
   - Click on any trace to see token usage and costs

## Model Pricing

LangSmith comes with built-in pricing for major models:
- GPT-4o, GPT-4o-mini, GPT-5 (OpenAI)
- Claude models (Anthropic)
- Gemini models (Google)

For custom pricing or models not in the default list:
1. Go to LangSmith UI → Settings → Models
2. Add your custom model pricing
3. Token costs will be calculated automatically

## Additional Resources

- [LangSmith Documentation](https://docs.langchain.com/langsmith)
- [Cost Tracking Guide](https://docs.langchain.com/langsmith/cost-tracking)
- [LangChain OpenAI Integration](https://python.langchain.com/docs/integrations/chat/openai)
