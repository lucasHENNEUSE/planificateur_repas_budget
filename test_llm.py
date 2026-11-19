"""
test_llm.py : tests des messages d'erreur de Gemini (carte #26).
Gemini est remplacé par un faux (@patch) : on provoque les erreurs nous-mêmes.
"""
import pytest
from unittest.mock import patch
from IA.llm_service import appeler_gemini_json, expliquer_erreur


def test_messages_clairs_selon_l_erreur():
    # Chaque erreur technique donne un message différent et compréhensible
    assert "Limite" in expliquer_erreur("429 RESOURCE_EXHAUSTED")
    assert "surchargé" in expliquer_erreur("503 UNAVAILABLE")
    assert "Clé API" in expliquer_erreur("400 API key not valid")
    assert "erreur" in expliquer_erreur("autre chose")


@patch("IA.llm_service.gemini_client")
def test_quota_atteint_leve_un_message_clair(client_gemini):
    # Erreur 429 : pas de nouvel essai, message sur la limite d'utilisation
    client_gemini.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")
    with pytest.raises(RuntimeError, match="Limite d'utilisation"):
        appeler_gemini_json("test")
    assert client_gemini.models.generate_content.call_count == 1


@patch("IA.llm_service.time.sleep")
@patch("IA.llm_service.gemini_client")
def test_gemini_surcharge_3_essais_puis_message(client_gemini, attente):
    # Erreur 503 : on réessaie 3 fois (sans vraie attente), puis message sur la surcharge
    client_gemini.models.generate_content.side_effect = Exception("503 UNAVAILABLE")
    with pytest.raises(RuntimeError, match="surchargé"):
        appeler_gemini_json("test")
    assert client_gemini.models.generate_content.call_count == 3