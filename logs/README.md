# Run logs

Real runs of `scripts/run_examples.py` over the 20 examples, Gemma 3 1B IT (Q4_K_M GGUF, 806 MB) via llama-cpp-python 0.3.36, Linux x86_64, 8 CPUs, no GPU. Kept unedited, including the failures. Times are US Central (CDT).

| file | prompt version | model text kept | notes |
|---|---|---|---|
| `run-2026-10-12-1403-prompt-v1-single-call.jsonl` | one call, asks for `EXPLANATION:` + `REPLY:` | 0/20 | The 1B model skipped the explanation every time and often wrote **as the client** ("We've already processed the onboarding fee..."). Format check sent all 20 to the fixed text. |
| `run-2026-10-12-1404.jsonl` | two calls (explain, reply), zero-shot | 10/20 (one guard over both) | Guard caught a reply that said "Please send your online banking login details and a photo of your ID", replies agreeing to move to WhatsApp, and explanations calling a scam "a standard payment process". Several replies it let through were still bad (declining a normal Etsy buyer, "let's discuss this directly"), which led to the quality checks. |
| `run-2026-10-12-1406.jsonl` | two calls, two few-shot examples each, one guard over both + reply quality check | 5/20 | Few-shot fixed the explanation format, but explanations still called scams "standard" and every reply to a flagged message failed. Because one guard covered both halves, a good explanation was thrown away whenever the reply failed. |
| `run-2026-10-12-1407.jsonl` | same prompts, separate guards for explanation and reply for explanation and reply, reply quality check | explanations 16/20, replies 5/20 | Every reply drafted for a flagged message was rejected (e.g. "I'll process the invoice as per your instructions", "Please send the gift card codes to the platform", "let's connect via WhatsApp"). Model replies are only kept for the 5 normal messages. |

`pytest-2026-10-12.txt` is the full test run.

Note: generation with a fresh model load can differ slightly from a batch run that reuses the loaded model, so `demo/` output is not byte-identical to these logs.
