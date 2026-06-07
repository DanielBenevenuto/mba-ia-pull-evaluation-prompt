"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


PROMPTS_TO_PULL = [
    {
        "remote_name": "leonanluppi/bug_to_user_story_v1",
        "local_key": "bug_to_user_story_v1",
        "output_file": "prompts/bug_to_user_story_v1.yml",
        "description": "Prompt para converter relatos de bugs em User Stories",
        "tags": ["bug-analysis", "user-story", "product-management"],
    },
]


def _extract_messages(prompt_template) -> list:
    messages = []

    raw_messages = getattr(prompt_template, "messages", None)
    if not raw_messages:
        return messages

    for msg in raw_messages:
        role = type(msg).__name__.lower()
        if "system" in role:
            role_name = "system"
        elif "human" in role or "user" in role:
            role_name = "user"
        elif "ai" in role or "assistant" in role:
            role_name = "assistant"
        else:
            role_name = role

        template = getattr(msg, "prompt", None)
        content = getattr(template, "template", None) if template else None

        if content is None:
            content = getattr(msg, "content", "")

        messages.append({"role": role_name, "content": content})

    return messages


def _build_yaml_payload(prompt_template, meta: dict) -> dict:
    messages = _extract_messages(prompt_template)

    system_prompt = ""
    user_prompt = ""
    for m in messages:
        if m["role"] == "system" and not system_prompt:
            system_prompt = m["content"]
        elif m["role"] == "user" and not user_prompt:
            user_prompt = m["content"]

    payload = {
        meta["local_key"]: {
            "description": meta["description"],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "pulled_at": date.today().isoformat(),
            "source": meta["remote_name"],
            "tags": meta["tags"],
            "messages": messages,
        }
    }

    return payload


def pull_prompts_from_langsmith() -> bool:
    success_count = 0

    for meta in PROMPTS_TO_PULL:
        remote_name = meta["remote_name"]
        output_file = meta["output_file"]

        print(f"\n→ Puxando prompt: {remote_name}")

        try:
            prompt_template = hub.pull(remote_name)
        except Exception as e:
            error_msg = str(e).lower()
            print(f"   ❌ Erro ao puxar prompt '{remote_name}': {e}")

            if "unauthorized" in error_msg or "api key" in error_msg or "401" in error_msg:
                print("   ⚠️  Verifique LANGSMITH_API_KEY no .env")
            elif "not found" in error_msg or "404" in error_msg:
                print(f"   ⚠️  Prompt '{remote_name}' não foi encontrado no LangSmith Hub")
            continue

        payload = _build_yaml_payload(prompt_template, meta)

        if save_yaml(payload, output_file):
            print(f"   ✓ Prompt salvo em: {output_file}")
            success_count += 1
        else:
            print(f"   ❌ Falha ao salvar em {output_file}")

    return success_count == len(PROMPTS_TO_PULL)


def main():
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if pull_prompts_from_langsmith():
        print("\n✅ Pull concluído com sucesso!")
        print("\nPróximo passo: refatore o prompt em prompts/bug_to_user_story_v2.yml")
        return 0
    else:
        print("\n⚠️  Pull concluído com falhas. Veja mensagens acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
