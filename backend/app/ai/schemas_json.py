"""JSON schemas for Groq structured outputs.

Strict mode has two hard requirements: every property must be listed in
``required``, and every object must set ``additionalProperties: false``.
Miss either and the request is rejected. Streaming and tool use are not
supported alongside structured outputs.

Only ``openai/gpt-oss-20b`` (and Qwen 3) honour this in the model set used
here — not every hosted model does — which is why MCQ generation is routed to
GPT-OSS.
"""

from __future__ import annotations

from typing import Any

QUESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_text": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_index": {"type": "integer", "minimum": 0, "maximum": 3},
                    "explanation": {"type": "string"},
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                    },
                    "topic": {"type": "string"},
                },
                "required": [
                    "question_text",
                    "options",
                    "correct_index",
                    "explanation",
                    "difficulty",
                    "topic",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

MCQ_BATCH_SCHEMA: dict[str, Any] = {"name": "mcq_batch", "schema": QUESTION_SCHEMA}
