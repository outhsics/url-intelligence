from types import SimpleNamespace

from url_intelligence.analyzer import AIAnalyzer, _extract_anthropic_text, _extract_text_output


def test_extract_text_output_from_chat_completion_shape() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary":"ok"}'))]
    )
    assert _extract_text_output(response) == '{"summary":"ok"}'


def test_use_glm_compat_when_provider_is_glm() -> None:
    analyzer = object.__new__(AIAnalyzer)
    analyzer.provider = "glm"
    analyzer.base_url = ""
    assert analyzer._use_glm_compat() is True


def test_use_glm_compat_when_base_url_is_bigmodel() -> None:
    analyzer = object.__new__(AIAnalyzer)
    analyzer.provider = "openai"
    analyzer.base_url = "https://open.bigmodel.cn/api/paas/v4/"
    assert analyzer._use_glm_compat() is True


def test_extract_text_output_from_anthropic_shape() -> None:
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text='{"summary":"ok"}')])
    assert _extract_anthropic_text(response) == '{"summary":"ok"}'


def test_use_anthropic_when_provider_is_anthropic() -> None:
    analyzer = object.__new__(AIAnalyzer)
    analyzer.provider = "anthropic"
    assert analyzer._use_anthropic() is True
