from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.domain.auth import AuthenticatedUser
from app.domain.chat import ChatMessage, ChatRequest, ChatResponse, MemoryWriteRequest, ToolCallRecord
from app.domain.classification import IssueText
from app.domain.errors import DomainError, ToolFailureError
from app.domain.rag import RAGQuery
from app.infra.llm import LLMClient
from app.infra.model_client import ModelServerClient
from app.infra.redaction import redact_value
from app.infra.tracing import get_tracer
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService


class ChatService:
    def __init__(
        self,
        session: Session,
        llm: LLMClient | None = None,
        model_client: ModelServerClient | None = None,
    ) -> None:
        self.session = session
        self.llm = llm or LLMClient()
        self.model_client = model_client or ModelServerClient()
        self.memory = MemoryService(session)
        self.rag = RAGService(session)
        self.tracer = get_tracer(__name__)

    def chat(
        self,
        *,
        actor: AuthenticatedUser,
        payload: ChatRequest,
    ) -> ChatResponse:
        conversation_id = payload.conversation_id or self.memory.new_conversation_id()

        with self.tracer.start_as_current_span("chat.message") as span:
            span.set_attribute("user.id", actor.id)
            span.set_attribute("chat.conversation_id", conversation_id)

            previous_messages = self.memory.get_short_term_messages(
                user_id=actor.id,
                conversation_id=conversation_id,
            )

            recent_memory = self.memory.format_recent_memories(
                actor=actor,
                limit=8,
            )

            system_prompt = self._load_system_prompt().replace(
                "{{RECENT_MEMORY}}",
                recent_memory,
            )

            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ]

            for item in previous_messages:
                if item.role in {"user", "assistant"}:
                    messages.append(
                        {
                            "role": item.role,
                            "content": item.content,
                        }
                    )

            messages.append(
                {
                    "role": "user",
                    "content": payload.message,
                }
            )

            first = self.llm.chat_completion(
                messages=messages,
                tools=self._tool_schemas(),
                tool_choice="auto",
            )

            assistant_message = first["choices"][0]["message"]
            tool_calls = assistant_message.get("tool_calls") or []

            used_tools: list[ToolCallRecord] = []

            if tool_calls:
                messages.append(assistant_message)

                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    raw_args = tool_call["function"].get("arguments") or "{}"

                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}

                    result = self._execute_tool(
                        actor=actor,
                        name=tool_name,
                        arguments=args,
                        default_repo=payload.repo,
                    )

                    used_tools.append(
                        ToolCallRecord(
                            name=tool_name,
                            arguments=redact_value(args),
                            result=redact_value(result),
                        )
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": json.dumps(redact_value(result)),
                        }
                    )

                final = self.llm.chat_completion(
                    messages=messages,
                    tools=self._tool_schemas(),
                    tool_choice="none",
                )

                answer = final["choices"][0]["message"].get("content") or ""

            else:
                answer = assistant_message.get("content") or ""

            updated_short_term = [
                *previous_messages,
                ChatMessage(role="user", content=payload.message),
                ChatMessage(role="assistant", content=answer),
            ]

            self.memory.save_short_term_messages(
                user_id=actor.id,
                conversation_id=conversation_id,
                messages=updated_short_term,
            )

            span.set_attribute("chat.used_tools", ",".join(item.name for item in used_tools))
            span.set_attribute("chat.answer_chars", len(answer))

            return ChatResponse(
                conversation_id=conversation_id,
                answer=answer,
                used_tools=used_tools,
            )

    def _execute_tool(
        self,
        *,
        actor: AuthenticatedUser,
        name: str,
        arguments: dict[str, Any],
        default_repo: str | None,
    ) -> dict[str, Any]:
        try:
            with self.tracer.start_as_current_span(f"tool.{name}") as span:
                span.set_attribute("tool.name", name)

                if name == "classify_issue":
                    result = self.model_client.classify(
                        title=arguments.get("title", ""),
                        body=arguments.get("body", ""),
                    )
                    return result

                if name == "extract_entities":
                    result = self.model_client.extract_entities(
                        title=arguments.get("title", ""),
                        body=arguments.get("body", ""),
                    )
                    return result

                if name == "summarize_issue":
                    result = self.model_client.summarize(
                        title=arguments.get("title", ""),
                        body=arguments.get("body", ""),
                    )
                    return result

                if name == "rag_answer":
                    result = self.rag.answer(
                        RAGQuery(
                            question=arguments.get("question", ""),
                            repo=arguments.get("repo") or default_repo,
                            source_type=arguments.get("source_type"),
                            top_k=arguments.get("top_k", 5),
                            use_reranker=True,
                        )
                    )
                    return result.model_dump()

                if name == "write_memory":
                    memory = self.memory.write_memory(
                        actor=actor,
                        payload=MemoryWriteRequest(
                            content=arguments.get("content", ""),
                            memory_type=arguments.get("memory_type", "episodic"),
                        ),
                    )
                    return memory.model_dump(mode="json")

                raise ToolFailureError(f"Unknown tool: {name}")

        except DomainError as exc:
            return {
                "error": exc.code,
                "message": exc.message,
            }

        except Exception as exc:
            return {
                "error": "tool_failure",
                "message": f"{name} failed safely: {exc}",
            }

    def _load_system_prompt(self) -> str:
        path = Path("prompts/chat_system.md")

        if path.exists():
            return path.read_text(encoding="utf-8")

        return (
            "You are Maintainer's Copilot. Help maintainers triage issues. "
            "Use tools when useful. Never write long-term memory unless the user explicitly asks."
        )

    def _tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "classify_issue",
                    "description": "Classify a GitHub issue as bug, feature, docs, or question.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["title", "body"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_entities",
                    "description": "Extract code-shaped entities from an issue.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["title", "body"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_issue",
                    "description": "Summarize a GitHub issue or thread.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["title", "body"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "rag_answer",
                    "description": "Answer a maintainer question using the RAG corpus.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "repo": {"type": "string"},
                            "source_type": {
                                "type": "string",
                                "enum": ["issue", "docs"],
                            },
                            "top_k": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                            },
                        },
                        "required": ["question"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_memory",
                    "description": (
                        "Explicitly write a long-term memory only when the user asks you to remember something."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "memory_type": {
                                "type": "string",
                                "enum": ["episodic", "semantic", "procedural"],
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
        ]