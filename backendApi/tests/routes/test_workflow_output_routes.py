"""
Tests for the workflow output routes of routes/output.py (M2M credentials) and routes/api.py (route token).

Each route finds the output node, checks the access, resolves the workflow owner, runs the workflow
when the output file is missing, then returns the output data, filtered by the Drupal filters.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main  # noqa: F401  (routes/api.py imports app.main: import it first)
from app.models.interface.user_interface import UserConfig
from app.routes import api, output
from app.services.user_service import UserService
from app.services.workflow_service import WorkflowService

ROWS = [{"name": "a", "age": 10}, {"name": "b", "age": 20}, {"name": "c", "age": 30}]
NAME_IS_B = "filter[f][condition][path]=name&filter[f][condition][value]=b"


def _node(node_type, url="my-data", token="tok", node_id="n1"):
    data = {"urlInput": {"value": url}}
    if token:
        data["tokenInput"] = {"value": token}
    return SimpleNamespace(id=node_id, type=node_type, data=data)


def _workflow(*nodes, workflow_id="w1"):
    return SimpleNamespace(id=workflow_id, pschema=SimpleNamespace(nodes=list(nodes)))


def _owner(credentials=None):
    user = Mock()
    user.id = "owner"
    user.username = "owner"
    user.is_active = True
    user.config = UserConfig(credentials=credentials or {"x-api-key": "secret"})
    return user


# The four routes: path, node type, module, valid credentials, refused status
ROUTES = {
    "output_custom": ("/output/my-data", "PdcOutput", output, {"x-api-key": "secret"}, 401),
    "output_workflow": ("/output/workflow/w1", "PdcOutput", output, {"x-api-key": "secret"}, 401),
    "api_custom": ("/api/my-data", "ApiOutput", api, {"Authorization": "Bearer tok"}, 403),
    "api_workflow": ("/api/workflow/w1", "ApiOutput", api, {"Authorization": "Bearer tok"}, 403),
}


class Env:
    """Patched services of a route; the output file is a temporary file."""

    def __init__(self, route, tmp_path):
        self.path, self.node_type, self.module, self.headers, self.refused = ROUTES[route]
        self.node = _node(self.node_type)
        self.workflow = _workflow(_node("DataFileBlock", url=None, node_id="n0"), self.node)
        self.owner = _owner()
        self.output_file = tmp_path / "n1-output.json"
        self.workflows = [_workflow(_node(self.node_type, url="other", node_id="n9"), workflow_id="w9"),
                          self.workflow]
        self.get_user = AsyncMock(return_value=self.owner)
        self.execute = AsyncMock(side_effect=self._write_output)
        self.get_workflow = AsyncMock(return_value=self.workflow)
        self.all_users = AsyncMock(return_value=[_owner({"x-other": "z"}), self.owner])

    async def _write_output(self, workflow, current_user=None):
        self.output_file.write_text(json.dumps(ROWS))

    def write_output(self, rows=ROWS):
        self.output_file.write_text(json.dumps(rows))

    def get(self, client, headers=None, query=""):
        url = self.path + (f"?{query}" if query else "")
        return client.get(url, headers=self.headers if headers is None else headers)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api.router)
    app.include_router(output.router)
    return TestClient(app)


@pytest.fixture(params=list(ROUTES))
def env(request, tmp_path):
    env = Env(request.param, tmp_path)
    module = env.module
    with patch.object(WorkflowService, "get_workflows", AsyncMock(return_value=env.workflows)), \
            patch.object(WorkflowService, "get_workflow", env.get_workflow), \
            patch.object(UserService, "get_user_from_workflow", env.get_user), \
            patch.object(UserService, "get_all_users", env.all_users), \
            patch.object(module, "import_and_execute_workflow", env.execute), \
            patch.object(module, "get_user_output_path", return_value=str(env.output_file)) as output_path, \
            patch("app.utils.utils.settings.domain_whitelist", []):
        env.output_path = output_path
        env.route = request.param
        yield env


def test_success_without_filter(client, env):
    env.write_output()

    response = env.get(client)

    assert response.status_code == 200
    assert response.json() == ROWS
    env.execute.assert_not_called()
    env.output_path.assert_called_once_with("n1", env.owner)
    env.get_user.assert_awaited_once_with(env.workflow)


def test_success_with_filter(client, env):
    env.write_output()

    response = env.get(client, query=NAME_IS_B)

    assert response.status_code == 200
    assert response.json() == [{"name": "b", "age": 20}]


def test_query_without_filter_returns_everything(client, env):
    env.write_output()

    assert env.get(client, query="page=2").json() == ROWS


def test_missing_file_runs_the_workflow(client, env):
    response = env.get(client)

    assert response.status_code == 200
    assert response.json() == ROWS
    env.execute.assert_awaited_once_with(env.workflow, current_user=env.owner)


def test_file_still_missing_after_execution(client, env):
    env.execute.side_effect = None

    response = env.get(client)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate output file"


def test_execution_failure(client, env):
    env.execute.side_effect = RuntimeError("node failed")

    response = env.get(client)

    assert response.status_code == 500
    assert response.json()["detail"] == "Workflow execution failed: node failed"


def test_invalid_filter(client, env):
    env.write_output()

    response = env.get(client, query="filter[f][condition][path]=name&filter[f][condition][operator]=LIKE")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid filter parameters: Unsupported filter operator: 'LIKE'"


def test_filtering_error(client, env):
    env.write_output()

    response = env.get(client, query="filter[f][condition][path]=missing&filter[f][condition][value]=x")

    assert response.status_code == 500
    assert response.json()["detail"].startswith("Error filtering data: ")


def test_user_service_error(client, env):
    env.get_user.side_effect = RuntimeError("db down")

    response = env.get(client)

    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to verify workflow ownership"


@pytest.mark.parametrize("headers", [{}, {"x-api-key": "wrong", "Authorization": "Bearer wrong"}])
def test_invalid_credentials(client, env, headers):
    env.write_output()

    response = env.get(client, headers=headers)

    assert response.status_code == env.refused
    env.execute.assert_not_called()


def test_credentials_of_another_user_are_refused(client, env):
    if env.module is api:
        pytest.skip("the API routes check the token of the node, not the users")
    env.write_output()

    response = env.get(client, headers={"x-other": "z"})

    assert response.status_code == 401
    assert response.json()["detail"] == "No valid credentials found in headers"


def test_output_of_a_workflow_without_owner_is_refused(client, env):
    """Without owner there are no credentials to check: the output routes refuse instead of serving anyone."""
    if env.module is api:
        pytest.skip("the API routes check the token of the node, not the users")
    env.write_output()
    env.get_user.return_value = None

    response = env.get(client)

    assert response.status_code == 401
    assert response.json()["detail"] == "No valid credentials found in headers"
    env.output_path.assert_not_called()
    env.execute.assert_not_called()


def test_access_check_position(client, env):
    """The API routes check the token before resolving the owner, the output routes after."""
    env.get_user.side_effect = RuntimeError("db down")

    response = env.get(client, headers={})

    if env.route == "output_workflow":
        # The credentials are first checked against all the users
        assert response.status_code == 401
    elif env.module is api:
        assert response.status_code == 403
    else:
        assert response.status_code == 503


def test_node_not_found(client, env):
    env.node.data["urlInput"]["value"] = "elsewhere"
    env.node.type = "OtherOutput"

    response = env.get(client)

    if env.route.endswith("custom"):
        assert response.status_code == 404
        expected = ("No PdcOutput node with this URL found" if env.module is output
                    else "No data found with this URL")
    else:
        assert response.status_code == 400
        expected = f"{env.node_type} node not found"
    assert response.json()["detail"] == expected


def test_custom_path_uses_the_first_matching_workflow(client, env):
    if not env.route.endswith("custom"):
        pytest.skip("custom path routes only")
    second = _node(env.node_type, node_id="n2")
    env.workflows.append(_workflow(second, workflow_id="w2"))
    env.write_output()

    env.get(client)

    env.output_path.assert_called_once_with("n1", env.owner)
    env.get_user.assert_awaited_once_with(env.workflow)


def test_workflow_not_found(client, env):
    if env.route.endswith("custom"):
        pytest.skip("workflow routes only")
    env.get_workflow.return_value = None

    response = env.get(client)

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found"


def test_unexpected_error(client, env):
    with patch.object(WorkflowService, "get_workflows", AsyncMock(side_effect=RuntimeError("boom"))):
        env.get_workflow.side_effect = RuntimeError("boom")

        response = env.get(client)

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error: boom"


def test_api_node_without_token_needs_a_whitelisted_origin(client, env):
    if env.module is not api:
        pytest.skip("API routes only")
    del env.node.data["tokenInput"]
    env.write_output()

    assert env.get(client).status_code == 403
    with patch("app.utils.utils.settings.domain_whitelist", ["example.com"]):
        assert env.get(client, headers={"origin": "https://example.com"}).status_code == 200

