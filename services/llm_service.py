import os
import time
from llama_cpp import Llama
from flask import current_app

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
MODEL_FILENAME = 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

_llm = None


def _detect_gpu_support():
    """Check if llama-cpp-python has GPU support."""
    try:
        from llama_cpp.llama_cpp import llama_supports_gpu_offload
        return llama_supports_gpu_offload()
    except Exception:
        return False


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

    gpu_supported = _detect_gpu_support()
    n_cores = os.cpu_count() or 4
    
    # Performance tuning: 
    # - Using min(8, cores - 1) provides best balance for llama.cpp on Windows
    # - n_ctx=1024 is plenty for these lessons and speeds up processing
    threads = min(8, max(1, n_cores - 1))
    n_ctx = 1024

    try:
        print(f"[HW] GPU Offload: {'ENABLED' if gpu_supported else 'DISABLED'}")
        print(f"[HW] Cores: {n_cores} | Threads: {threads} | Context: {n_ctx}")

        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=n_ctx,
            n_threads=threads,
            n_threads_batch=threads,
            n_gpu_layers=-1 if gpu_supported else 0, # -1 offloads all layers to GPU
            n_batch=512,
            verbose=False,
            seed=42 # Consistent results for testing
        )
        print("[HW] Model initialization SUCCESS")

    except Exception as e:
        print(f"[HW] LLM Init Error: {e}")
        # Fallback to CPU-only if GPU initialization fails
        if gpu_supported:
            print("[HW] Retrying with CPU-only...")
            try:
                _llm = Llama(
                    model_path=MODEL_PATH,
                    n_ctx=n_ctx,
                    n_threads=threads,
                    n_gpu_layers=0,
                    verbose=False
                )
                return _llm
            except Exception as e2:
                print(f"[HW] Critical Fallback Error: {e2}")
        raise e

    return _llm


def query_llm(prompt, stream=False, max_tokens=300):
    try:
        model = _get_llm()

        messages = [
            {"role": "system", "content": "You are a helpful and knowledgeable AI educational assistant. Follow instructions precisely."},
            {"role": "user", "content": prompt}
        ]

        params = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stream": stream,
        }

        if stream:
            def stream_wrapper():
                for chunk in model.create_chat_completion(**params):
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        yield {'choices': [{'text': content}]}
            return stream_wrapper()

        start = time.time()
        result = model.create_chat_completion(**params)
        
        elapsed = round(time.time() - start, 2)
        response = result['choices'][0]['message'].get('content', '').strip()
        print(f"[DEBUG] Generation Time: {elapsed}s")
        return response

    except Exception as e:
        print(f"[DEBUG] Model ERROR: {str(e)}")
        return f"Error: {str(e)}"

