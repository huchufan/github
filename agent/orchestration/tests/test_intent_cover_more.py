import pytest

from agent.orchestration.core.intent import IntentRecognizer, ParameterExtractor
from agent.core.types import Intent, ParameterDef
from agent.core.errors import ParameterValidationError


def test_tokenize_and_extract_entities():
    ir = IntentRecognizer()
    tokens = ir.tokenize("请在 2026-09-13 上传文件 /tmp/report.pdf 到 http://example.com")
    assert "2026-09-13" in tokens or "2026-09-13" in " ".join(tokens)
    entities = ir.extract_entities(tokens)
    assert "urls" in entities and entities["urls"][0].startswith("http")
    assert "paths" in entities and "/tmp/report.pdf" in entities["paths"]


def test_classify_and_top_intent():
    i1 = Intent(name="send_mail", keywords=["send", "mail"], required_parameters=[], optional_parameters=[], complexity="low")
    i2 = Intent(name="analyze", keywords=["analyze", "data"], required_parameters=[], optional_parameters=[], complexity="low")
    ir = IntentRecognizer(intents=[i1, i2])
    tokens = ir.tokenize("please send this mail to user@example.com")
    scores = ir.classify_intent(tokens)
    assert "send_mail" in scores and "analyze" in scores
    top = ir.get_top_intent(scores)
    assert top == "send_mail"
    top_n = ir.get_top_n_intents(scores, n=2)
    assert len(top_n) == 2


def test_get_intent_and_infer_domain_and_clarification():
    i = Intent(name="intent_generate_code", keywords=["gen", "code"], required_parameters=[], optional_parameters=[], complexity="high")
    ir = IntentRecognizer(intents=[i])
    assert ir.get_intent("intent_generate_code") is i
    domain = ir._infer_domain("intent_generate_code")
    assert domain == "code"
    # generate clarification when missing params
    qs = ir.generate_clarification_questions("intent_generate_code", {"a": None})
    assert isinstance(qs, list) and len(qs) == 1


def test_extract_simple_parameters_defaults_applied():
    p = ParameterDef(name="n", type="number", default=42)
    intent = Intent(name="I", keywords=[], required_parameters=[p], optional_parameters=[] , complexity="low")
    ir = IntentRecognizer(intents=[intent])
    params = ir._extract_simple_parameters(intent, "")
    assert params.get("n") == 42


def test_parameter_extractor_missing_required_and_validation_error():
    # missing required should be reported
    p1 = ParameterDef(name="m", type="number")
    intent1 = Intent(name="I1", keywords=[], required_parameters=[p1], optional_parameters=[], complexity="low")
    pe = ParameterExtractor()
    ps = pe.extract_and_validate_parameters(intent1, "no digits here", {})
    assert not ps.complete and "m" in ps.missing_required

    # validation failure: default present but invalid type -> raises ParameterValidationError
    p2 = ParameterDef(name="b", type="boolean", default="notabool")
    intent2 = Intent(name="I2", keywords=[], required_parameters=[p2], optional_parameters=[], complexity="low")
    with pytest.raises(ParameterValidationError):
        pe.extract_and_validate_parameters(intent2, "", {})
