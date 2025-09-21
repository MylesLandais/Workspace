# Qwen3-Coder: How to Run Locally

Qwen3-Coder is Qwen’s new series of coding agent models, available in 30B (**Qwen3-Coder-Flash**) and 480B parameters. **Qwen3-480B-A35B-Instruct** achieves SOTA coding performance rivalling Claude Sonnet-4, GPT-4.1, and [Kimi K2](https://docs.unsloth.ai/models/kimi-k2-how-to-run-locally), with 61.8% on Aider Polygot and support for 256K (extendable to 1M) token context.

We also uploaded Qwen3-Coder with native <mark style="background-color:purple;">**1M context length**</mark> extended by YaRN and full-precision 8bit and 16bit versions. [Unsloth](https://github.com/unslothai/unsloth) also now supports fine-tuning and [RL](https://docs.unsloth.ai/basics/reinforcement-learning-rl-guide) of Qwen3-Coder.

{% hint style="success" %}
[**UPDATE:** We fixed tool-calling for Qwen3-Coder! ](#tool-calling-fixes)You can now use tool-calling seamlessly in llama.cpp, Ollama, LMStudio, Open WebUI, Jan etc. This issue was universal and affected all uploads (not just Unsloth), and we've communicated with the Qwen team about our fixes! [Read more](#tool-calling-fixes)
{% endhint %}

<a href="#run-qwen3-coder-30b-a3b-instruct" class="button secondary">Run 30B-A3B</a><a href="#run-qwen3-coder-480b-a35b-instruct" class="button secondary">Run 480B-A35B</a>

{% hint style="success" %}
**Does** [**Unsloth Dynamic Quants**](https://docs.unsloth.ai/models/unsloth-dynamic-2.0-ggufs) **work?** Yes, and very well. In third-party testing on the Aider Polyglot benchmark, the **UD-Q4\_K\_XL (276GB)** dynamic quant nearly matched the **full bf16 (960GB)** Qwen3-coder model, scoring 60.9% vs 61.8%. [More details here.](https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF/discussions/8)
{% endhint %}

#### **Qwen3 Coder - Unsloth Dynamic 2.0 GGUFs**:

| Dynamic 2.0 GGUF (to run)                                                                                                                                                                                                     | 1M Context Dynamic 2.0 GGUF                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <ul><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF">30B-A3B-Instruct</a></li><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF">480B-A35B-Instruct</a></li></ul> | <ul><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF">30B-A3B-Instruct</a></li><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-1M-GGUF">480B-A35B-Instruct</a></li></ul> |

## 🖥️ **Running Qwen3-Coder**

Below are guides for the [**30B-A3B**](#run-qwen3-coder-30b-a3b-instruct) and [**480B-A35B**](#run-qwen3-coder-480b-a35b-instruct) variants of the model.

### :gear: Recommended Settings

Qwen recommends these inference settings for both models:

`temperature=0.7`, `top_p=0.8`, `top_k=20`, `repetition_penalty=1.05`

* <mark style="background-color:green;">**Temperature of 0.7**</mark>
* Top\_K of 20
* Min\_P of 0.00 (optional, but 0.01 works well, llama.cpp default is 0.1)
* Top\_P of 0.8
* <mark style="background-color:green;">**Repetition Penalty of 1.05**</mark>
* Chat template:&#x20;

  {% code overflow="wrap" %}

  ```
  <|im_start|>user
  Hey there!<|im_end|>
  <|im_start|>assistant
  What is 1+1?<|im_end|>
  <|im_start|>user
  2<|im_end|>
  <|im_start|>assistant
  ```

  {% endcode %}
* Recommended context output: 65,536 tokens (can be increased). Details here.

**Chat template/prompt format with newlines un-rendered**

{% code overflow="wrap" %}

```
<|im_start|>user\nHey there!<|im_end|>\n<|im_start|>assistant\nWhat is 1+1?<|im_end|>\n<|im_start|>user\n2<|im_end|>\n<|im_start|>assistant\n
```

{% endcode %}

<mark style="background-color:yellow;">**Chat template for tool calling**</mark> (Getting the current temperature for San Francisco). More details here for how to format tool calls.

```
<|im_start|>user
What's the temperature in San Francisco now? How about tomorrow?<|im_end|>
<|im_start|>assistant
<tool_call>\n<function=get_current_temperature>\n<parameter=location>\nSan Francisco, CA, USA
</parameter>\n</function>\n</tool_call><|im_end|>
<|im_start|>user
<tool_response>
{"temperature": 26.1, "location": "San Francisco, CA, USA", "unit": "celsius"}
</tool_response>\n<|im_end|>
```

{% hint style="info" %}
Reminder that this model supports only non-thinking mode and does not generate `<think></think>` blocks in its output. Meanwhile, specifying `enable_thinking=False` is no longer required.
{% endhint %}

### Run Qwen3-Coder-30B-A3B-Instruct:

To achieve inference speeds of 6+ tokens per second for our Dynamic 4-bit quant, have at least **18GB of unified memory** (combined VRAM and RAM) or **18GB of system RAM** alone. As a rule of thumb, your available memory should match or exceed the size of the model you’re using. E.g. the UD\_Q8\_K\_XL quant (full precision), which is 32.5GB, will require at least **33GB of unified memory** (VRAM + RAM) or **33GB of RAM** for optimal performance.

**NOTE:** The model can run on less memory than its total size, but this will slow down inference. Maximum memory is only needed for the fastest speeds.

Given that this is a non thinking model, there is no need to set `thinking=False` and the model does not generate `<think> </think>` blocks.

{% hint style="info" %}
Follow the [**best practices above**](#recommended-settings). They're the same as the 480B model.
{% endhint %}

#### 🦙 Ollama: Run Qwen3-Coder-30B-A3B-Instruct Tutorial

1. Install `ollama` if you haven't already! You can only run models up to 32B in size.

```bash
apt-get update
apt-get install pciutils -y
curl -fsSL https://ollama.com/install.sh | sh
```

2. Run the model! Note you can call `ollama serve`in another terminal if it fails! We include all our fixes and suggested parameters (temperature etc) in `params` in our Hugging Face upload!

```bash
ollama run hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL
```

#### :sparkles: Llama.cpp: Run Qwen3-Coder-30B-A3B-Instruct Tutorial

1. Obtain the latest `llama.cpp` on [GitHub here](https://github.com/ggml-org/llama.cpp). You can follow the build instructions below as well. Change `-DGGML_CUDA=ON` to `-DGGML_CUDA=OFF` if you don't have a GPU or just want CPU inference.

```bash
apt-get update
apt-get install pciutils build-essential cmake curl libcurl4-openssl-dev -y
git clone https://github.com/ggml-org/llama.cpp
cmake llama.cpp -B llama.cpp/build \
    -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build llama.cpp/build --config Release -j --clean-first --target llama-cli llama-gguf-split
cp llama.cpp/build/bin/llama-* llama.cpp
```

2. You can directly pull from HuggingFace via:

   ```
   ./llama.cpp/llama-cli \
       -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_XL \
       --jinja -ngl 99 --threads -1 --ctx-size 32684 \
       --temp 0.7 --min-p 0.0 --top-p 0.80 --top-k 20 --repeat-penalty 1.05
   ```
3. Download the model via (after installing `pip install huggingface_hub hf_transfer` ). You can choose UD\_Q4\_K\_XL or other quantized versions.

```python
# !pip install huggingface_hub hf_transfer
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id = "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    local_dir = "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    allow_patterns = ["*UD-Q4_K_XL*"],
)
```

### Run Qwen3-Coder-480B-A35B-Instruct:

To achieve inference speeds of 6+ tokens per second for our 1-bit quant, we recommend at least **150GB of unified memory** (combined VRAM and RAM) or **150GB of system RAM** alone. As a rule of thumb, your available memory should match or exceed the size of the model you’re using. E.g. the Q2\_K\_XL quant, which is 180GB, will require at least **180GB of unified memory** (VRAM + RAM) or **180GB of RAM** for optimal performance.

**NOTE:** The model can run on less memory than its total size, but this will slow down inference. Maximum memory is only needed for the fastest speeds.

{% hint style="info" %}
Follow the [**best practices above**](#recommended-settings).  They're the same as the 30B model.
{% endhint %}

#### 📖 Llama.cpp: Run Qwen3-Coder-480B-A35B-Instruct Tutorial

For Coder-480B-A35B, we will specifically use Llama.cpp for optimized inference and a plethora of options.

{% hint style="success" %}
If you want a **full precision unquantized version**, use our `Q8_K_XL, Q8_0` or `BF16` versions!
{% endhint %}

1. Obtain the latest `llama.cpp` on [GitHub here](https://github.com/ggml-org/llama.cpp). You can follow the build instructions below as well. Change `-DGGML_CUDA=ON` to `-DGGML_CUDA=OFF` if you don't have a GPU or just want CPU inference.

   ```bash
   apt-get update
   apt-get install pciutils build-essential cmake curl libcurl4-openssl-dev -y
   git clone https://github.com/ggml-org/llama.cpp
   cmake llama.cpp -B llama.cpp/build \
       -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON
   cmake --build llama.cpp/build --config Release -j --clean-first --target llama-cli llama-gguf-split
   cp llama.cpp/build/bin/llama-* llama.cpp
   ```

2. You can directly use llama.cpp to download the model but I normally suggest using `huggingface_hub` To use llama.cpp directly, do:

   {% code overflow="wrap" %}

   ```bash
   ./llama.cpp/llama-cli \
       -hf unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF:Q2_K_XL \
       --threads -1 \
       --ctx-size 16384 \
       --n-gpu-layers 99 \
       -ot ".ffn_.*_exps.=CPU" \
       --temp 0.7 \
       --min-p 0.0 \
       --top-p 0.8 \
       --top-k 20 \
       --repeat-penalty 1.05
   ```

   {% endcode %}

3. Or, download the model via (after installing `pip install huggingface_hub hf_transfer` ). You can choose UD-Q2\_K\_XL, or other quantized versions..

   ```python
   # !pip install huggingface_hub hf_transfer
   import os
   os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0" # Can sometimes rate limit, so set to 0 to disable
   from huggingface_hub import snapshot_download
   snapshot_download(
       repo_id = "unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF",
       local_dir = "unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF",
       allow_patterns = ["*UD-Q2_K_XL*"],
   )
   ```

4. Run the model in conversation mode and try any prompt.

5. Edit `--threads -1` for the number of CPU threads, `--ctx-size` 262114 for context length, `--n-gpu-layers 99` for GPU offloading on how many layers. Try adjusting it if your GPU goes out of memory. Also remove it if you have CPU only inference.

{% hint style="success" %}
Use `-ot ".ffn_.*_exps.=CPU"` to offload all MoE layers to the CPU! This effectively allows you to fit all non MoE layers on 1  GPU, improving generation speeds. You can customize the regex expression to fit more layers if you have more GPU capacity. More options discussed [here](#improving-generation-speed).
{% endhint %}

{% code overflow="wrap" %}

```bash
./llama.cpp/llama-cli \
    --model unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF/UD-Q2_K_XL/Qwen3-Coder-480B-A35B-Instruct-UD-Q2_K_XL-00001-of-00004.gguf \
    --threads -1 \
    --ctx-size 16384 \
    --n-gpu-layers 99 \
    -ot ".ffn_.*_exps.=CPU" \
    --temp 0.7 \
    --min-p 0.0 \
    --top-p 0.8 \
    --top-k 20 \
    --repeat-penalty 1.05
```

{% endcode %}

{% hint style="success" %}
Also don't forget about the new Qwen3 update. Run [**Qwen3-235B-A22B-Instruct-2507**](https://docs.unsloth.ai/models/qwen3-how-to-run-and-fine-tune/qwen3-2507) locally with llama.cpp.
{% endhint %}

#### :tools: Improving generation speed

If you have more VRAM, you can try offloading more MoE layers, or offloading whole layers themselves.

Normally, `-ot ".ffn_.*_exps.=CPU"`  offloads all MoE layers to the CPU! This effectively allows you to fit all non MoE layers on 1 GPU, improving generation speeds. You can customize the regex expression to fit more layers if you have more GPU capacity.

If you have a bit more GPU memory, try `-ot ".ffn_(up|down)_exps.=CPU"` This offloads up and down projection MoE layers.

Try `-ot ".ffn_(up)_exps.=CPU"` if you have even more GPU memory. This offloads only up projection MoE layers.

You can also customize the regex, for example `-ot "\.(6|7|8|9|[0-9][0-9]|[0-9][0-9][0-9])\.ffn_(gate|up|down)_exps.=CPU"` means to offload gate, up and down MoE layers but only from the 6th layer onwards.

The [latest llama.cpp release](https://github.com/ggml-org/llama.cpp/pull/14363) also introduces high throughput mode. Use `llama-parallel`. Read more about it [here](https://github.com/ggml-org/llama.cpp/tree/master/examples/parallel). You can also **quantize the KV cache to 4bits** for example to reduce VRAM / RAM movement, which can also make the generation process faster.

#### :triangular\_ruler:How to fit long context (256K to 1M)

To fit longer context, you can use <mark style="background-color:green;">**KV cache quantization**</mark> to quantize the K and V caches to lower bits. This can also increase generation speed due to reduced RAM / VRAM data movement. The allowed options for K quantization (default is `f16`) include the below.

`--cache-type-k f32, f16, bf16, q8_0, q4_0, q4_1, iq4_nl, q5_0, q5_1`&#x20;

You should use the `_1` variants for somewhat increased accuracy, albeit it's slightly slower. For eg `q4_1, q5_1`&#x20;

You can also quantize the V cache, but you will need to <mark style="background-color:yellow;">**compile llama.cpp with Flash Attention**</mark> support via `-DGGML_CUDA_FA_ALL_QUANTS=ON`, and use `--flash-attn` to enable it.

We also uploaded 1 million context length GGUFs via YaRN scaling [here](https://app.gitbook.com/o/HpyELzcNe0topgVLGCZY/s/xhOjnexMCB3dmuQFQ2Zq/).

## :toolbox: Tool Calling Fixes

We managed to fix tool calling via `llama.cpp --jinja` specifically for serving through `llama-server`! If you’re downloading our 30B-A3B quants, no need to worry as these already include our fixes. For the 480B-A35B model, please:

1. Download the first file at <https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF/tree/main/UD-Q2\\_K\\_XL> for UD-Q2\_K\_XL, and replace your current file
2. Use `snapshot_download` as usual as in <https://docs.unsloth.ai/basics/qwen3-coder-how-to-run-locally#llama.cpp-run-qwen3-tutorial> which will auto override the old files
3. Use the new chat template via `--chat-template-file`. See [GGUF chat template](https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF?chat_template=default) or [chat\_template.jinja](https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct/raw/main/chat_template.jinja)
4. As an extra, we also made 1 single 150GB UD-IQ1\_M file (so Ollama works) at <https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF/blob/main/Qwen3-Coder-480B-A35B-Instruct-UD-IQ1\\_M.gguf>

This should solve issues like: <https://github.com/ggml-org/llama.cpp/issues/14915>

### Using Tool Calling

To format the prompts for tool calling, let's showcase it with an example.

I created a Python function called `get_current_temperature` which is a function which should get the current temperature for a location. For now we created a placeholder function which will always return 21.6 degrees celsius. You should change this to a true function!!

{% code overflow="wrap" %}

```python
def get_current_temperature(location: str, unit: str = "celsius"):
    """Get current temperature at a location.

    Args:
        location: The location to get the temperature for, in the format "City, State, Country".
        unit: The unit to return the temperature in. Defaults to "celsius". (choices: ["celsius", "fahrenheit"])

    Returns:
        the temperature, the location, and the unit in a dict
    """
    return {
        "temperature": 26.1, # PRE_CONFIGURED -> you change this!
        "location": location,
        "unit": unit,
    }
```

{% endcode %}

Then use the tokenizer to create the entire prompt:

{% code overflow="wrap" %}

```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("unsloth/Qwen3-Coder-480B-A35B-Instruct")

messages = [
    {'role': 'user', 'content': "What's the temperature in San Francisco now? How about tomorrow?"},
    {'content': "", 'role': 'assistant', 'function_call': None, 'tool_calls': [
        {'id': 'ID', 'function': {'arguments': {"location": "San Francisco, CA, USA"}, 'name': 'get_current_temperature'}, 'type': 'function'},
    ]},
    {'role': 'tool', 'content': '{"temperature": 26.1, "location": "San Francisco, CA, USA", "unit": "celsius"}', 'tool_call_id': 'ID'},
]

prompt = tokenizer.apply_chat_template(messages, tokenize = False)
```

{% endcode %}

## :bulb:Performance Benchmarks

{% hint style="info" %}
These official benchmarks are for the full BF16 checkpoint. To use this, simply use the `Q8_K_XL, Q8_0, BF16` checkpoints we uploaded - you can still use the tricks like MoE offloading for these versions as well!
{% endhint %}

Here are the benchmarks for the 480B model:

#### Agentic Coding

<table data-full-width="true"><thead><tr><th>Benchmark</th><th>Qwen3‑Coder 40B‑A35B‑Instruct</th><th>Kimi‑K2</th><th>DeepSeek‑V3-0324</th><th>Claude 4 Sonnet</th><th>GPT‑4.1</th></tr></thead><tbody><tr><td>Terminal‑Bench</td><td><strong>37.5</strong></td><td>30.0</td><td>2.5</td><td>35.5</td><td>25.3</td></tr><tr><td>SWE‑bench Verified w/ OpenHands (500 turns)</td><td><strong>69.6</strong></td><td>–</td><td>–</td><td>70.4</td><td>–</td></tr><tr><td>SWE‑bench Verified w/ OpenHands (100 turns)</td><td><strong>67.0</strong></td><td>65.4</td><td>38.8</td><td>68.0</td><td>48.6</td></tr><tr><td>SWE‑bench Verified w/ Private Scaffolding</td><td>–</td><td>65.8</td><td>–</td><td>72.7</td><td>63.8</td></tr><tr><td>SWE‑bench Live</td><td><strong>26.3</strong></td><td>22.3</td><td>13.0</td><td>27.7</td><td>–</td></tr><tr><td>SWE‑bench Multilingual</td><td><strong>54.7</strong></td><td>47.3</td><td>13.0</td><td>53.3</td><td>31.5</td></tr><tr><td>Multi‑SWE‑bench mini</td><td><strong>25.8</strong></td><td>19.8</td><td>7.5</td><td>24.8</td><td>–</td></tr><tr><td>Multi‑SWE‑bench flash</td><td><strong>27.0</strong></td><td>20.7</td><td>–</td><td>25.0</td><td>–</td></tr><tr><td>Aider‑Polyglot</td><td><strong>61.8</strong></td><td>60.0</td><td>56.9</td><td>56.4</td><td>52.4</td></tr><tr><td>Spider2</td><td><strong>31.1</strong></td><td>25.2</td><td>12.8</td><td>31.1</td><td>16.5</td></tr></tbody></table>

#### Agentic Browser Use

<table data-full-width="true"><thead><tr><th>Benchmark</th><th>Qwen3‑Coder 40B‑A35B‑Instruct</th><th>Kimi‑K2</th><th>DeepSeek‑V3 0324</th><th>Claude Sonnet‑4</th><th>GPT‑4.1</th></tr></thead><tbody><tr><td>WebArena</td><td><strong>49.9</strong></td><td>47.4</td><td>40.0</td><td>51.1</td><td>44.3</td></tr><tr><td>Mind2Web</td><td><strong>55.8</strong></td><td>42.7</td><td>36.0</td><td>47.4</td><td>49.6</td></tr></tbody></table>

#### Agentic Tool -Use

<table data-full-width="true"><thead><tr><th>Benchmark</th><th>Qwen3‑Coder 40B‑A35B‑Instruct</th><th>Kimi‑K2</th><th>DeepSeek‑V3 0324</th><th>Claude Sonnet‑4</th><th>GPT‑4.1</th></tr></thead><tbody><tr><td>BFCL‑v3</td><td><strong>68.7</strong></td><td>65.2</td><td>56.9</td><td>73.3</td><td>62.9</td></tr><tr><td>TAU‑Bench Retail</td><td><strong>77.5</strong></td><td>70.7</td><td>59.1</td><td>80.5</td><td>–</td></tr><tr><td>TAU‑Bench Airline</td><td><strong>60.0</strong></td><td>53.5</td><td>40.0</td><td>60.0</td><td>–</td></tr></tbody></table>
