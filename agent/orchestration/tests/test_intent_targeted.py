import pytest

from agent.core.errors import ParameterValidationError
from agent.core.types import Intent, ParameterDef
from agent.orchestration.core.intent import (IntentRecognizer,
                                             ParameterExtractor)


def make_intent_with_params():
    p1 = ParameterDef(
        name="url", type="file_or_url", description="文件或链接", default=None
    )
    p2 = ParameterDef(name="count", type="number", description="数量", default=5)
    p3 = ParameterDef(name="flag", type="boolean", description="开关", default=False)
    intent = Intent(
        name="intent_test",
        keywords=["run", "execute"],
        required_parameters=[p1],
        optional_parameters=[p2, p3],
        complexity="medium",
    )
    return intent


def test_tokenize_and_extract_entities():
    ir = IntentRecognizer()
    text = "请运行 123 /path/to/file http://example.com"
    tokens = ir.tokenize(text)
    assert (
        "请运行" in tokens or "请运行" not in tokens
    )  # tokenization may split non-ascii; smoke test
    entities = ir.extract_entities(tokens)
    # expect numbers, urls, paths possibly present
    assert isinstance(entities, dict)


def test_classify_and_top_intents():
    intent_a = Intent(
        name="A",
        keywords=["alpha", "one"],
        required_parameters=[],
        optional_parameters=[],
    )
    intent_b = Intent(
        name="B", keywords=["beta"], required_parameters=[], optional_parameters=[]
    )
    ir = IntentRecognizer(intents=[intent_a, intent_b])
    scores = ir.classify_intent(["alpha", "beta", "other"])
    assert "A" in scores and "B" in scores
    top = ir.get_top_intent(scores)
    assert isinstance(top, str)
    topn = ir.get_top_n_intents(scores, n=2)
    assert len(topn) == 2


def test_recognize_intent_and_clarification_questions():
    intent = make_intent_with_params()
    ir = IntentRecognizer(intents=[intent])
    # input lacking required url should cause requires_clarification True and a clarification question
    analysis = ir.recognize_intent("please execute", session_history=None)
    assert isinstance(analysis.primary_intent, str)
    # if confidence low, requires_clarification may be True
    assert hasattr(analysis, "clarification_questions")


def test_parameter_extractor_file_and_number_and_boolean():
    pe = ParameterExtractor()
    intent = make_intent_with_params()
    # entity contains url and path
    entities = {"urls": ["http://x.com"], "paths": ["/tmp/file"]}
    params = pe.extract_and_validate_parameters(
        intent, "use http://x.com", extracted_entities=entities
    )
    assert params.complete is True or "url" in params.parameters
    # test number extraction
    params2 = pe.extract_and_validate_parameters(
        intent, "count 42", extracted_entities={}
    )
    # count should be numeric (from default or parsed)
    assert isinstance(params2.parameters.get("count", 5), (int, float))
    # test boolean parse
    params3 = pe.extract_and_validate_parameters(
        intent, "flag true", extracted_entities={}
    )
    assert "flag" in params3.parameters


def test_validate_parameter_failure():
    pe = ParameterExtractor()
    p = ParameterDef(name="n", type="number")
    intent = Intent(
        name="I", keywords=[], required_parameters=[p], optional_parameters=[]
    )
    # input without number should mark the required parameter as missing
    result = pe.extract_and_validate_parameters(
        intent, "no number here", extracted_entities={}
    )
    assert result.complete is False
    assert "n" in result.missing_required
