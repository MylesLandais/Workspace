```
---------------------------------------------------------------------------
ModuleNotFoundError                       Traceback (most recent call last)
Cell In[2], line 22
     19 from dotenv import load_dotenv
     21 from google.adk.agents import LlmAgent
---> 22 from google.adk.models.lite_llm import LiteLlm
     23 from google.adk.runners import Runner
     24 from google.adk.sessions import InMemorySessionService

File /opt/conda/lib/python3.11/site-packages/google/adk/models/lite_llm.py:38
     35 import warnings
     37 from google.genai import types
---> 38 import litellm
     39 from litellm import acompletion
     40 from litellm import ChatCompletionAssistantMessage

ModuleNotFoundError: No module named 'litellm'
```


