# Functional Testing & Evaluation

Test script: [test_qa.py](test_qa.py). Run with `python test_qa.py`.

## Results

| Question | Type | Top score | Time | Result |
|---|---|---|---|---|
| What is the divide and conquer technique? | answerable | 0.664 | 36.8s | Correct, detailed answer from `documents/` |
| What is a greedy algorithm? | answerable | 0.706 | 23.9s | Correct, detailed answer |
| What is mathematical induction used for? | answerable | 0.656 | 27.4s | Correct, detailed answer |
| What is the capital of France? | unanswerable | 0.204 | 0.4s | Correctly refused ("I don't have information...") |
| How do I bake a chocolate cake? | unanswerable | 0.285 | 0.4s | Correctly refused |
| Tell me everything. | vague | 0.320 | 0.4s | Correctly refused |
| *(empty string)* | edge case | — | — | CLI exits the loop before calling `answer_query` — verified via `main.py`, no crash |

## Key finding: relevance gating

Initial testing (before the fix) showed the chat model answering unanswerable questions from its own general knowledge instead of refusing, even though the retrieved chunks were clearly irrelevant. Comparing top similarity scores made the problem visible:

- Unanswerable questions: **0.20 – 0.32**
- Answerable questions: **0.66 – 0.71**

The gap is wide and consistent, so `main.py` now checks the top chunk's score against `RELEVANCE_THRESHOLD = 0.4` before calling the LLM at all. Below the threshold, it returns a canned "I don't have information about that" answer directly — instant (0.4s) and never hallucinates, instead of relying on the small model to follow the "answer only from context" system prompt (which it did not reliably do).

## Response time

The plan's estimate (~1–3s/question) assumes GPU/NPU acceleration. This machine runs `phi-3.5-mini` on CPU only, so answerable questions take **24–37s** (one outlier took ~115s for a long, verbose answer). This is a hardware/model limitation, not a bug. Possible optimizations if needed: a smaller chat model, retrieving fewer chunks (lower `TOP_K`), or shorter max-token responses.

## Transient error handling

One test run hit `FoundryLocalException: Operation was cancelled` on a single request; it did not reproduce across 3 repeated attempts of the same question in isolation, with no competing processes. Treated as a transient native-runtime hiccup. `main.py` now wraps `complete_chat` in a retry (`CHAT_RETRIES = 2`) so a one-off cancellation doesn't crash the whole session.
