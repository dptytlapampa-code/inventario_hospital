from app.routes import search
from app.services import search_service


def test_global_search_across_datasets():
    dataset = [
        {"tipo": "Equipo", "nombre": "Notebook", "numero_serie": "ABC"},
        {"tipo": "Insumo", "nombre": "Mouse", "numero_serie": "XYZ"},
        {"tipo": "Usuario", "nombre": "Alice", "email": "alice@example.com"},
    ]

    results = search_service.global_search("notebook", dataset)
    assert len(results) == 1
    assert results[0]["tipo"] == "Equipo"

    user_results = search_service.global_search("alice", dataset)
    assert len(user_results) == 1
    assert user_results[0]["tipo"] == "Usuario"


def test_paginate_helper():
    items = list(range(1, 26))
    assert search.paginate(items, page=1, per_page=10) == list(range(1, 11))
    assert search.paginate(items, page=3, per_page=10) == list(range(21, 26))
