"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    assert PROMPT_FILE.exists(), f"Arquivo de prompt não encontrado: {PROMPT_FILE}"
    data = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' ausente no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' ausente"
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip(), "'system_prompt' está vazio"
        assert len(system_prompt) > 200, "'system_prompt' parece curto demais para um prompt otimizado"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        role_markers = [
            "você é",
            "voce e",
            "persona",
            "product manager",
            "atue como",
            "você atua",
        ]
        assert any(marker in system_prompt for marker in role_markers), (
            f"system_prompt não define uma persona. Esperado um dos marcadores: {role_markers}"
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        mentions_markdown = "markdown" in system_prompt
        mentions_user_story_template = (
            "como [ator" in system_prompt
            or "como um [" in system_prompt
            or "eu quero" in system_prompt
            or "para que" in system_prompt
        )
        mentions_acceptance = (
            "critérios de aceitação" in system_prompt
            or "criterios de aceitacao" in system_prompt
            or "given/when/then" in system_prompt
            or "dado que" in system_prompt
        )

        assert mentions_markdown or mentions_user_story_template, (
            "system_prompt não menciona Markdown nem o template padrão de user story"
        )
        assert mentions_acceptance, (
            "system_prompt não menciona critérios de aceitação / Given-When-Then"
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        has_examples_section = (
            "exemplo" in system_prompt
            or "few-shot" in system_prompt
            or "few shot" in system_prompt
        )
        has_input_output_markers = (
            "entrada:" in system_prompt and "saída:" in system_prompt
        ) or (
            "entrada:" in system_prompt and "saida:" in system_prompt
        ) or (
            "input:" in system_prompt and "output:" in system_prompt
        )

        assert has_examples_section, (
            "system_prompt não contém uma seção de exemplos (Few-shot)"
        )
        assert has_input_output_markers, (
            "Exemplos devem deixar claros os pares entrada/saída"
        )

        # Pelo menos 2 exemplos para configurar Few-shot
        example_count = system_prompt.count("entrada:")
        assert example_count >= 2, (
            f"Few-shot precisa de pelo menos 2 exemplos, encontrados: {example_count}"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("system_prompt", "user_prompt", "description"):
            value = prompt_data.get(field, "") or ""
            assert "[TODO]" not in value, f"Campo '{field}' ainda contém [TODO]"
            assert "[todo]" not in value.lower(), f"Campo '{field}' ainda contém [todo]"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied")
        assert techniques is not None, (
            "Metadado 'techniques_applied' ausente no YAML"
        )
        assert isinstance(techniques, list), (
            "'techniques_applied' deve ser uma lista"
        )
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )

        # Few-shot é obrigatório pelo enunciado
        techniques_lower = [t.lower() for t in techniques]
        assert any("few" in t and "shot" in t for t in techniques_lower), (
            "Few-shot Learning é obrigatório e deve constar em techniques_applied"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
