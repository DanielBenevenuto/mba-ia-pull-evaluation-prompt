"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


PROMPTS_TO_PUSH = [
    {
        "yaml_path": "prompts/bug_to_user_story_v2.yml",
        "yaml_key": "bug_to_user_story_v2",
        "hub_slug": "bug_to_user_story_v2",
    },
]


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version", "techniques_applied"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    user_prompt = (prompt_data.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("system_prompt está vazio")
    if not user_prompt:
        errors.append("user_prompt está vazio")

    if "[TODO]" in system_prompt or "[TODO]" in user_prompt:
        errors.append("Prompt ainda contém [TODO]")

    if "{bug_report}" not in user_prompt and "{bug_report}" not in system_prompt:
        errors.append("Prompt precisa conter a variável {bug_report}")

    techniques = prompt_data.get("techniques_applied") or []
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas em techniques_applied (encontradas: {len(techniques)})")

    return (len(errors) == 0, errors)


def _build_chat_template(prompt_data: dict) -> ChatPromptTemplate:
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data["user_prompt"]

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    print(f"\n→ Validando prompt: {prompt_name}")

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("   ❌ Validação falhou:")
        for err in errors:
            print(f"      - {err}")
        return False
    print("   ✓ Validação OK")

    chat_template = _build_chat_template(prompt_data)

    description_parts = [prompt_data.get("description", "").strip()]
    techniques = prompt_data.get("techniques_applied") or []
    if techniques:
        description_parts.append("Técnicas aplicadas: " + ", ".join(techniques) + ".")
    description = " ".join(p for p in description_parts if p)

    tags = list(prompt_data.get("tags") or [])
    for tech in techniques:
        slug = tech.lower().replace(" ", "-")
        if slug not in tags:
            tags.append(slug)

    print(f"   → Publicando em: {prompt_name}")

    push_kwargs = {
        "description": description,
        "tags": tags,
        "is_public": True,
    }

    try:
        url = hub.push(prompt_name, chat_template, **push_kwargs)
    except TypeError:
        try:
            url = hub.push(prompt_name, chat_template, description=description, tags=tags)
            print("   ⚠️  Versão do langchain não suporta is_public via API.")
            print("   ⚠️  Torne o prompt público manualmente no dashboard do LangSmith.")
        except Exception as e:
            print(f"   ❌ Erro ao publicar: {e}")
            return False
    except Exception as e:
        error_msg = str(e).lower()
        print(f"   ❌ Erro ao publicar: {e}")
        if "unauthorized" in error_msg or "api key" in error_msg or "401" in error_msg:
            print("   ⚠️  Verifique LANGSMITH_API_KEY no .env")
        elif "forbidden" in error_msg or "403" in error_msg:
            print("   ⚠️  Verifique se o USERNAME_LANGSMITH_HUB corresponde ao seu workspace")
        return False

    print(f"   ✓ Publicado com sucesso!")
    if url:
        print(f"   🔗 URL: {url}")
    return True


def main():
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    success_count = 0

    for meta in PROMPTS_TO_PUSH:
        yaml_path = meta["yaml_path"]
        yaml_key = meta["yaml_key"]

        print(f"\n📄 Carregando: {yaml_path}")
        data = load_yaml(yaml_path)

        if not data:
            print(f"   ❌ Não foi possível carregar {yaml_path}")
            continue

        prompt_data = data.get(yaml_key)
        if not prompt_data:
            print(f"   ❌ Chave '{yaml_key}' não encontrada em {yaml_path}")
            continue

        full_name = f"{username}/{meta['hub_slug']}"

        if push_prompt_to_langsmith(full_name, prompt_data):
            success_count += 1

    print("\n" + "=" * 50)
    if success_count == len(PROMPTS_TO_PUSH):
        print(f"✅ {success_count}/{len(PROMPTS_TO_PUSH)} prompts publicados com sucesso!")
        print("\nPróximo passo: python src/evaluate.py")
        return 0
    else:
        print(f"⚠️  {success_count}/{len(PROMPTS_TO_PUSH)} prompts publicados")
        return 1


if __name__ == "__main__":
    sys.exit(main())
