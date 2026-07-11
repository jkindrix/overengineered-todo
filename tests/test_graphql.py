"""Tests for the GraphQL transport (ADR-0018) — a third adapter over one core."""

from __future__ import annotations

import json

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def _gql(client: Client, query: str, variables: dict | None = None):
    return client.post(
        "/graphql/",
        data=json.dumps({"query": query, "variables": variables or {}}),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_create_and_query(client):
    resp = _gql(
        client,
        'mutation { createTask(title:"gql", priority:"HIGH"){ id title status priority } }',
    )
    assert resp.status_code == 200
    created = resp.json()["data"]["createTask"]
    assert (created["title"], created["status"], created["priority"]) == (
        "gql",
        "draft",
        "HIGH",
    )

    got = _gql(
        client,
        "query($id:String!){ task(id:$id){ title status } }",
        {"id": created["id"]},
    ).json()["data"]["task"]
    assert got == {"title": "gql", "status": "draft"}


@pytest.mark.django_db
def test_lifecycle_and_filtered_list(client):
    tid = _gql(client, 'mutation{ createTask(title:"flow"){ id } }').json()["data"][
        "createTask"
    ]["id"]
    _gql(
        client,
        'mutation($id:String!){ transitionTask(id:$id, targetStatus:"active"){ status } }',
        {"id": tid},
    )
    rows = _gql(client, 'query{ tasks(status:"active"){ title status } }').json()[
        "data"
    ]["tasks"]
    assert any(t["title"] == "flow" and t["status"] == "active" for t in rows)


@pytest.mark.django_db
def test_illegal_transition_surfaces_graphql_error(client):
    tid = _gql(client, 'mutation{ createTask(title:"x"){ id } }').json()["data"][
        "createTask"
    ]["id"]
    body = _gql(
        client,
        'mutation($id:String!){ transitionTask(id:$id, targetStatus:"completed"){ status } }',
        {"id": tid},
    ).json()
    assert "errors" in body
    assert "Cannot transition" in body["errors"][0]["message"]


@pytest.mark.django_db
def test_delete(client):
    tid = _gql(client, 'mutation{ createTask(title:"del"){ id } }').json()["data"][
        "createTask"
    ]["id"]
    deleted = _gql(
        client, "mutation($id:String!){ deleteTask(id:$id) }", {"id": tid}
    ).json()["data"]["deleteTask"]
    assert deleted is True
    # It's gone: a follow-up query reports an error (not found).
    assert (
        "errors"
        in _gql(
            client, "query($id:String!){ task(id:$id){ title } }", {"id": tid}
        ).json()
    )
