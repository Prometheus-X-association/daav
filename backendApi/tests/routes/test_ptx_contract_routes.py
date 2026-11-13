"""
Behaviour of the Prometheus-X contract, data exchange and input routes (PDC and catalog mocked).
"""
import json
import os
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.interface.dataset_interface import FileDataset, PTXDataset
from app.routes import ptx

pytestmark = pytest.mark.asyncio

CONFIG = {"catalogUri": "https://catalog/", "contractUri": "https://contract/", "endpoint": "https://pdc/"}
USER = Mock(username="alice")
DATA_PROVIDER_ROLE = "Data provider for Organisational Data"
DATA_PROVIDER_ROLE_URL = (
    "https://registry.visionstrust.com/static/references/roles/dataProviderForOrganisationalData.json"
)


def ptx_connection():
    return PTXDataset.model_construct(id=None, type="ptx", name="p", url="https://pdc.example", token="token")


def http_response(status_code=200, json_data=None, text=""):
    response = Mock(status_code=status_code, text=text)
    response.json.return_value = json_data
    return response


def contracts_url(participant_id):
    return f"https://contract/contracts/for/{ptx.b64_encode(f'https://catalog/catalog/participants/{participant_id}')}"


class FakeAsyncClient:
    """Stands in for httpx.AsyncClient: serves the responses by URL and records the requests."""

    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None, timeout=None):
        self.requests.append((url, params))
        return self.responses[url]


def routes_context(participants, **patches):
    """Patch the connection, its configuration and its participants, plus the given attributes of the module."""
    stack = ExitStack()
    stack.enter_context(patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())))
    stack.enter_context(patch.object(ptx, "get_private_configuration", AsyncMock(return_value=CONFIG)))
    stack.enter_context(patch.object(ptx, "get_participants_id_from_connection", AsyncMock(return_value=participants)))
    for name, value in patches.items():
        stack.enter_context(patch.object(ptx, name, value))
    return stack


# ===========================
# USE CASE CONTRACTS
# ===========================

def use_case_contract(contract_id="c1", ecosystem="https://eco/1", orchestrator="https://catalog/participants/me"):
    return Mock(id=contract_id, ecosystem=ecosystem, orchestrator=orchestrator, dataProviders=[], purposes=[],
                logo=None)


def ecosystem_participant(participant, roles, *offerings):
    return Mock(participant=participant, roles=roles, offerings=[Mock(serviceOffering=o) for o in offerings])


def offering(name, data_resources=(), software_resources=()):
    service = Mock(dataResources=list(data_resources), softwareResources=list(software_resources))
    service.name = name
    return service


def offering_url(offering_id):
    return f"https://catalog/catalog/serviceofferings/{offering_id}"


class UseCase:
    """One participant ("me") whose contracts endpoint returns the given contracts of one ecosystem."""

    def __init__(self, contracts, ecosystem, offerings=None, orchestrator_details=None, participants=("me",)):
        self.contracts = contracts
        self.client = FakeAsyncClient({
            contracts_url(p): http_response(json_data={"contracts": [{} for _ in contracts]}) for p in participants
        })
        self.participants = list(participants)
        self.fetch_ecosystem = AsyncMock(return_value=ecosystem)
        self.fetch_participant = AsyncMock(return_value=orchestrator_details)
        self.fetch_offering = AsyncMock(side_effect=lambda client, url: (offerings or {}).get(url))

    async def run(self, **kwargs):
        with routes_context(self.participants, httpx=Mock(AsyncClient=self.client)), \
             patch.object(ptx.PdcContract, "model_validate", side_effect=self.contracts * len(self.participants)), \
             patch.object(ptx.pdc_service, "fetch_ecosystem_async", self.fetch_ecosystem), \
             patch.object(ptx.pdc_service, "fetch_participant_async", self.fetch_participant), \
             patch.object(ptx.pdc_service, "fetch_service_offering_async", self.fetch_offering):
            return await ptx.get_use_case_contract("connection-id", USER, **kwargs)


def orchestrated_ecosystem(*participants, invitations=()):
    ecosystem = Mock(orchestrator="me", participants=list(participants),
                     invitations=[{"participant": p, "status": s} for p, s in invitations])
    ecosystem.name = "Ecosystem 1"
    return ecosystem


class TestUseCaseContracts:

    async def test_contract_orchestrated_by_the_participant_is_returned_with_name_and_logo(self):
        contract = use_case_contract()
        case = UseCase([contract], orchestrated_ecosystem(), orchestrator_details={"logo": "logo.png"})
        assert await case.run() == [contract]
        assert (contract.name, contract.logo) == ("Ecosystem 1", "logo.png")
        case.fetch_ecosystem.assert_awaited_once_with(case.client, "https://eco/1")
        case.fetch_participant.assert_awaited_once_with(case.client, "https://catalog/participants/me")
        assert case.client.requests == [(contracts_url("me"), {})]

    @pytest.mark.parametrize("has_signed, params", [(True, {"hasSigned": "true"}), (False, {"hasSigned": "false"})])
    async def test_signed_filter_is_sent_to_the_contract_service(self, has_signed, params):
        case = UseCase([use_case_contract()], orchestrated_ecosystem())
        await case.run(has_signed=has_signed)
        assert case.client.requests == [(contracts_url("me"), params)]

    @pytest.mark.parametrize("details, logo", [(None, ""), ({}, "")])
    async def test_orchestrator_without_logo_gives_an_empty_logo(self, details, logo):
        contract = use_case_contract()
        await UseCase([contract], orchestrated_ecosystem(), orchestrator_details=details).run()
        assert contract.logo == logo

    async def test_contract_without_orchestrator_keeps_its_logo(self):
        contract = use_case_contract(orchestrator=None)
        case = UseCase([contract], orchestrated_ecosystem())
        assert await case.run() == [contract]
        case.fetch_participant.assert_not_awaited()
        assert contract.logo is None

    async def test_contract_orchestrated_by_someone_else_is_left_out(self):
        ecosystem = orchestrated_ecosystem()
        ecosystem.orchestrator = "someone-else"
        case = UseCase([use_case_contract()], ecosystem)
        assert await case.run() == []
        case.fetch_participant.assert_not_awaited()

    async def test_contract_without_ecosystem_is_left_out(self):
        case = UseCase([use_case_contract(ecosystem=None), use_case_contract("c2")], orchestrated_ecosystem())
        result = await case.run()
        assert [contract.id for contract in result] == ["c2"]
        case.fetch_ecosystem.assert_awaited_once()

    async def test_failing_contract_does_not_stop_the_others(self):
        good = use_case_contract("c2")
        case = UseCase([use_case_contract("c1"), good], orchestrated_ecosystem())
        case.fetch_ecosystem.side_effect = [RuntimeError("catalog down"), orchestrated_ecosystem()]
        assert await case.run() == [good]

    async def test_contract_added_before_a_failure_is_kept(self):
        contract = use_case_contract()
        ecosystem = orchestrated_ecosystem(ecosystem_participant("me", [], "purpose"))
        case = UseCase([contract], ecosystem)
        case.fetch_offering.side_effect = RuntimeError("catalog down")
        assert await case.run() == [contract]
        assert contract.purposes == []

    async def test_refused_contract_request_is_skipped(self):
        contract = use_case_contract()
        case = UseCase([contract], orchestrated_ecosystem(), participants=("other", "me"))
        case.client.responses[contracts_url("other")] = http_response(status_code=500)
        case.contracts = [contract]
        with routes_context(["other", "me"], httpx=Mock(AsyncClient=case.client)), \
             patch.object(ptx.PdcContract, "model_validate", side_effect=[contract]), \
             patch.object(ptx.pdc_service, "fetch_ecosystem_async", case.fetch_ecosystem), \
             patch.object(ptx.pdc_service, "fetch_participant_async", case.fetch_participant):
            assert await ptx.get_use_case_contract("connection-id", USER) == [contract]

    async def test_data_providers_are_the_offerings_of_the_other_signed_data_providers(self):
        contract = use_case_contract()
        ecosystem = orchestrated_ecosystem(
            ecosystem_participant("no-role", [], "o-no-role"),
            ecosystem_participant("role", [DATA_PROVIDER_ROLE], "o-role"),
            ecosystem_participant("role-url", [DATA_PROVIDER_ROLE_URL], "o-role-url-1", "o-role-url-2"),
            ecosystem_participant("other-role", ["Service provider"], "o-other-role"),
            ecosystem_participant("unsigned", [], "o-unsigned"),
            ecosystem_participant("pending", [], "o-pending"),
            ecosystem_participant("me", [], "o-me"),
            invitations=[("no-role", "Signed"), ("role", "Signed"), ("role-url", "Signed"), ("other-role", "Signed"),
                         ("pending", "Pending"), ("me", "Signed")],
        )
        offerings = {offering_url(o): offering(o, data_resources=["r"])
                     for o in ("o-no-role", "o-role", "o-role-url-1", "o-role-url-2", "o-other-role", "o-unsigned",
                               "o-pending", "o-me")}
        await UseCase([contract], ecosystem, offerings).run()
        assert [o.name for o in contract.dataProviders] == ["o-no-role", "o-role", "o-role-url-1", "o-role-url-2"]

    async def test_data_providers_without_data_resources_are_left_out(self):
        contract = use_case_contract()
        ecosystem = orchestrated_ecosystem(ecosystem_participant("p", [], "with", "without", "none", "missing"),
                                           invitations=[("p", "Signed")])
        without_resources = offering("none")
        without_resources.dataResources = None
        offerings = {offering_url("with"): offering("with", data_resources=["r"]),
                     offering_url("without"): offering("without"),
                     offering_url("none"): without_resources}
        await UseCase([contract], ecosystem, offerings).run()
        assert [o.name for o in contract.dataProviders] == ["with"]

    async def test_purposes_are_the_offerings_of_the_participant_with_software_resources(self):
        contract = use_case_contract()
        ecosystem = orchestrated_ecosystem(ecosystem_participant("me", ["Service provider"], "software", "data-only"),
                                           ecosystem_participant("p", [], "other"),
                                           invitations=[("p", "Signed")])
        offerings = {offering_url("software"): offering("software", software_resources=["s"]),
                     offering_url("data-only"): offering("data-only", data_resources=["r"]),
                     offering_url("other"): offering("other", data_resources=["r"], software_resources=["s"])}
        await UseCase([contract], ecosystem, offerings).run()
        assert [o.name for o in contract.purposes] == ["software"]
        assert [o.name for o in contract.dataProviders] == ["other"]

    async def test_contracts_of_every_participant_are_gathered(self):
        first, second = use_case_contract("c1"), use_case_contract("c2")
        ecosystem = orchestrated_ecosystem()
        client = FakeAsyncClient({contracts_url(p): http_response(json_data={"contracts": [{}]}) for p in ("me", "p2")})
        ecosystems = [ecosystem, Mock(orchestrator="p2", name="Ecosystem 2", participants=[], invitations=[])]
        with routes_context(["me", "p2"], httpx=Mock(AsyncClient=client)), \
             patch.object(ptx.PdcContract, "model_validate", side_effect=[first, second]), \
             patch.object(ptx.pdc_service, "fetch_ecosystem_async", AsyncMock(side_effect=ecosystems)), \
             patch.object(ptx.pdc_service, "fetch_participant_async", AsyncMock(return_value=None)):
            assert await ptx.get_use_case_contract("connection-id", USER) == [first, second]


# ===========================
# SERVICE CHAINS
# ===========================

class TestServiceChains:

    async def run(self, participants, responses, contracts, ecosystems):
        with routes_context(participants), \
             patch.object(ptx.requests, "get", side_effect=responses) as get, \
             patch.object(ptx.PdcContract, "model_validate", side_effect=contracts), \
             patch.object(ptx.pdc_service, "fetch_ecosystem", side_effect=ecosystems) as fetch_ecosystem:
            result = await ptx.get_service_chain("connection-id", USER, timeout_seconds=40)
        return result, get, fetch_ecosystem

    async def test_service_chains_of_the_orchestrated_contracts_are_returned(self):
        contracts = [Mock(id="c1", ecosystem="https://eco/1"), Mock(id="c2", ecosystem="https://eco/2")]
        ecosystems = [Mock(orchestrator="me", serviceChains=["chain-1"]), Mock(orchestrator="other", serviceChains=["x"])]
        result, get, fetch_ecosystem = await self.run(
            ["me"], [http_response(json_data={"contracts": [{}, {}]})], contracts, ecosystems)
        assert result == [{"contract_id": "c1", "service_chains": ["chain-1"]}]
        get.assert_called_once_with(contracts_url("me"), timeout=40)
        fetch_ecosystem.assert_any_call("https://eco/1", timeout=40)

    async def test_refused_contract_request_is_skipped(self):
        result, get, _ = await self.run(
            ["other", "me"], [http_response(status_code=404), http_response(json_data={"contracts": [{}]})],
            [Mock(id="c1", ecosystem="https://eco/1")], [Mock(orchestrator="me", serviceChains=[])])
        assert result == [{"contract_id": "c1", "service_chains": []}]
        assert get.call_count == 2

    async def test_contract_without_ecosystem_or_failing_is_skipped(self):
        contracts = [Mock(id="c1", ecosystem=None), Mock(id="c2", ecosystem="https://eco/2"),
                     Mock(id="c3", ecosystem="https://eco/3")]
        ecosystems = [RuntimeError("catalog down"), Mock(orchestrator="me", serviceChains=["chain-3"])]
        result, _, fetch_ecosystem = await self.run(
            ["me"], [http_response(json_data={"contracts": [{}, {}, {}]})], contracts, ecosystems)
        assert result == [{"contract_id": "c3", "service_chains": ["chain-3"]}]
        assert fetch_ecosystem.call_count == 2


# ===========================
# DATA EXCHANGES
# ===========================

def exchange(exchange_id, resources=("r1",), status="IMPORT_SUCCESS", contract="c1", **values):
    return {"_id": exchange_id, "status": status, "contract": contract,
            "resources": [{"resource": f"https://catalog/{r}"} for r in resources], **values}


def resource_payload(resource_id, produced_by=""):
    return {"_id": resource_id, "name": f"Resource {resource_id}", "description": "d", "attributes": [],
            "producedBy": produced_by, "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"}


def resource_details(resource_id, owner=(None, None)):
    return {"id": resource_id, "name": f"Resource {resource_id}", "description": "d",
            "owner": {"id": owner[0], "name": owner[1]}}


class TestDataExchanges:

    async def run(self, exchanges, resources=None, exchanges_status=200, fetch_participant=None):
        resources = resources or {}
        requested = []

        def fake_get(url, **kwargs):
            requested.append(url)
            if url == "https://pdc/dataexchanges":
                return http_response(exchanges_status, {"content": exchanges}, text="refused")
            resource = resources[url.rsplit("/", 1)[1]]
            if isinstance(resource, Exception):
                raise resource
            return resource

        with routes_context(None), \
             patch.object(ptx.requests, "get", side_effect=fake_get), \
             patch.object(ptx.pdc_service, "fetch_participant", fetch_participant or Mock()) as fetch:
            result = await ptx.get_data_exchanges("connection-id", Mock(), USER)
        return result["dataExchanges"], requested, fetch

    async def test_only_successful_imports_are_listed(self):
        exchanges = [exchange("e1", providerEndpoint="https://provider", createdAt="2026-01-01"),
                     exchange("e2", status="PENDING"), exchange("e3", status=None)]
        result, _, _ = await self.run(exchanges, {"r1": http_response(json_data=resource_payload("r1"))})
        assert result == [{"resources": [resource_details("r1")], "contract": "c1",
                           "providerEndpoint": "https://provider",
                           "executions": [{"id": "e1", "createdAt": "2026-01-01"}]}]

    async def test_exchanges_of_the_same_resources_contract_and_endpoint_are_grouped_latest_first(self):
        exchanges = [exchange("old", ("r1", "r2"), providerEndpoint="https://provider", createdAt="2026-01-01"),
                     exchange("undated", ("r2", "r1"), providerEndpoint="https://provider"),
                     exchange("new", ("r1", "r2"), providerEndpoint="https://provider", createdAt="2026-03-01"),
                     exchange("other-contract", ("r1", "r2"), contract="c2", providerEndpoint="https://provider"),
                     exchange("other-endpoint", ("r1", "r2"), consumerEndpoint="https://consumer"),
                     exchange("other-resources", ("r1",), providerEndpoint="https://provider")]
        resources = {r: http_response(json_data=resource_payload(r)) for r in ("r1", "r2")}
        result, requested, _ = await self.run(exchanges, resources)
        assert [[execution["id"] for execution in group["executions"]] for group in result] == [
            ["new", "old", "undated"], ["other-contract"], ["other-endpoint"], ["other-resources"]]
        assert result[0]["executions"][2] == {"id": "undated"}
        assert [resource["id"] for resource in result[0]["resources"]] == ["r1", "r2"]
        assert result[2]["consumerEndpoint"] == "https://consumer"
        assert "providerEndpoint" not in result[2]
        # Each resource is requested once
        assert sorted(requested) == ["https://catalog/r1", "https://catalog/r2", "https://pdc/dataexchanges"]

    async def test_provider_endpoint_wins_over_consumer_endpoint(self):
        exchanges = [exchange("e1", providerEndpoint="https://provider", consumerEndpoint="https://consumer")]
        result, _, _ = await self.run(exchanges, {"r1": http_response(json_data=resource_payload("r1"))})
        assert result[0]["providerEndpoint"] == "https://provider"
        assert "consumerEndpoint" not in result[0]

    async def test_resource_owner_is_fetched_from_the_catalog(self):
        owner = Mock(id="owner-1", legalName="Owner")
        fetch_participant = Mock(return_value=owner)
        result, _, fetch = await self.run([exchange("e1")],
                                          {"r1": http_response(json_data=resource_payload("r1", "owner-1"))},
                                          fetch_participant=fetch_participant)
        assert result[0]["resources"] == [resource_details("r1", ("owner-1", "Owner"))]
        fetch.assert_called_once_with("https://catalog/participants/owner-1", timeout=30)

    async def test_unknown_owner_gives_empty_owner_details(self):
        result, _, _ = await self.run([exchange("e1")],
                                      {"r1": http_response(json_data=resource_payload("r1", "owner-1"))},
                                      fetch_participant=Mock(return_value=None))
        assert result[0]["resources"] == [resource_details("r1")]

    async def test_resources_that_cannot_be_fetched_are_left_out(self):
        resources = {"r1": http_response(status_code=404), "r2": RuntimeError("catalog down"),
                     "r3": http_response(json_data={"invalid": True}), "r4": http_response(json_data=resource_payload("r4"))}
        result, requested, _ = await self.run([exchange("e1", ("r1", "r2", "r3", "r4")), exchange("e2", ("r1",))],
                                              resources)
        assert [[resource["id"] for resource in group["resources"]] for group in result] == [["r4"], []]
        # A failed resource is not cached: it is requested again
        assert requested.count("https://catalog/r1") == 2

    async def test_exchange_without_resources_is_listed(self):
        result, _, _ = await self.run([{"_id": "e1", "status": "IMPORT_SUCCESS"}])
        assert result == [{"resources": [], "contract": None, "executions": [{"id": "e1"}]}]

    async def test_no_exchange_gives_an_empty_list(self):
        result, _, _ = await self.run([])
        assert result == []

    async def test_refused_history_keeps_the_pdc_status_code(self):
        with pytest.raises(HTTPException) as error:
            await self.run([], exchanges_status=403)
        assert (error.value.status_code, error.value.detail) == (403, "Can't retrieve data exchange history: refused")

    async def test_unexpected_error_is_a_500(self):
        request = Mock()
        with routes_context(None), patch.object(ptx.requests, "get", side_effect=RuntimeError("pdc down")):
            with pytest.raises(HTTPException) as error:
                await ptx.get_data_exchanges("connection-id", request, USER)
        assert (error.value.status_code, error.value.detail) == (500, "Internal server error: pdc down")


# ===========================
# BILATERAL CONTRACTS
# ===========================

def bilaterals_url(participant_id):
    return f"https://contract//bilaterals/for/{ptx.b64_encode(f'https://catalog/catalog/participants/{participant_id}')}"


class TestBilateralContracts:

    async def run(self, participants, responses, contracts, infos):
        with routes_context(participants), \
             patch.object(ptx.requests, "get", side_effect=responses) as get, \
             patch.object(ptx.PdcContractBilateral, "model_validate", side_effect=contracts), \
             patch.object(ptx.pdc_service, "get_provider_name_and_img_from_contract", side_effect=infos):
            result = await ptx.get_billateral_contract("connection-id", USER, timeout_seconds=40)
        return result, get

    async def test_contracts_of_every_participant_are_returned_with_the_endpoints(self):
        first, second = Mock(), Mock()
        result, get = await self.run(
            ["p1", "p2"],
            [http_response(json_data={"contracts": [{}]}), http_response(json_data={"contracts": [{}]})],
            [first, second], [{"name": "Provider", "img": "logo.png"}, {"name": "", "img": None}])
        assert result == {"contracts": [first, second], "endpoint": "https://pdc/", "contractUri": "https://contract/"}
        assert (first.name, first.img) == ("Provider", "logo.png")
        assert (second.name, second.img) == ("Unknown", "")
        assert [call.args[0] for call in get.call_args_list] == [bilaterals_url("p1"), bilaterals_url("p2")]
        assert get.call_args.kwargs == {"timeout": 40}

    async def test_refused_request_and_failing_contract_are_skipped(self):
        good = Mock()
        result, _ = await self.run(
            ["p1", "p2"],
            [http_response(status_code=500), http_response(json_data={"contracts": [{}, {}]})],
            [ValueError("invalid contract"), good], [{"name": "Provider", "img": "logo.png"}])
        assert result["contracts"] == [good]

    async def test_connection_lookup_error_is_a_500(self):
        with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(side_effect=RuntimeError("database down"))):
            with pytest.raises(HTTPException) as error:
                await ptx.get_billateral_contract("connection-id", USER)
        assert (error.value.status_code, error.value.detail) == (500, "Error finding connection: database down")

    @pytest.mark.parametrize("config", [{"contractUri": "https://contract/"}, {"catalogUri": "https://catalog/"}])
    async def test_incomplete_configuration_is_a_500(self, config):
        with patch.object(ptx.dataset_service, "get_dataset", AsyncMock(return_value=ptx_connection())), \
             patch.object(ptx, "get_private_configuration", AsyncMock(return_value=config)):
            with pytest.raises(HTTPException) as error:
                await ptx.get_billateral_contract("connection-id", USER)
        assert error.value.status_code == 500
        assert error.value.detail == "Error loading private configuration: Missing catalogUri or contractUri in config"

    async def test_participants_are_looked_up_with_the_default_timeout(self):
        with routes_context(["p1"]) , patch.object(ptx.requests, "get", return_value=http_response(status_code=500)):
            await ptx.get_billateral_contract("connection-id", USER, timeout_seconds=40)
            ptx.get_participants_id_from_connection.assert_awaited_once_with("connection-id", USER)


# ===========================
# PDC INPUT
# ===========================

class PdcInput:
    """A PDC data exchange received for the given users, with the uploads written under tmp_path."""

    def __init__(self, tmp_path, users, content_type="application/json", body=b'{"a": 1}'):
        self.upload_dir = tmp_path
        self.auth = [{"user": user, "matched_credentials": ["cred"]} for user in users]
        self.request = Mock(headers={"Content-Type": content_type})
        self.request.body = AsyncMock(return_value=body)
        self.request.json = AsyncMock(side_effect=lambda: json.loads(body))
        self.datasets = {}
        self.add_connection = AsyncMock(side_effect=self._add_connection)
        self.edit_dataset = AsyncMock()
        self.provider_name = "Provider"

    async def _add_connection(self, dataset, user):
        dataset.id = f"new-{user.username}"

    async def _get_dataset(self, dataset_id, user):
        dataset = self.datasets[dataset_id]
        if isinstance(dataset, Exception):
            raise dataset
        return dataset

    def folder(self, user):
        return str(self.upload_dir / str(user.id))

    def existing(self, user, dataset_id="existing", name="Provider_c1", if_exist="replace", content=None, **values):
        os.makedirs(self.folder(user), exist_ok=True)
        path = os.path.join(self.folder(user), "previous.json")
        if content is not None:
            with open(path, "w") as file:
                file.write(content)
        fields = {"id": dataset_id, "type": "file", "name": name, "folder": self.folder(user), "filePath": path,
                  "ifExist": if_exist, **values}
        self.datasets[dataset_id] = FileDataset.model_construct(**fields)
        return self.datasets[dataset_id]

    async def run(self):
        with patch.object(ptx.user_service, "get_all_users", AsyncMock(return_value=[])), \
             patch.object(ptx, "authenticate_m2m_credentials", return_value=self.auth), \
             patch.object(ptx.pdc_service, "fetch_contract", return_value=Mock(id="c1")) as self.fetch_contract, \
             patch.object(ptx.pdc_service, "get_provider_name_from_contract", return_value=self.provider_name), \
             patch.object(ptx.dataset_service, "get_dataset", AsyncMock(side_effect=self._get_dataset)), \
             patch.object(ptx.dataset_service, "add_connection", self.add_connection), \
             patch.object(ptx.dataset_service, "edit_dataset", self.edit_dataset), \
             patch.object(ptx.settings, "upload_dir", str(self.upload_dir)), \
             patch.object(ptx.time, "time", return_value=1700000000.5):
            return await ptx.read_input(self.request, Mock(), Mock(x_ptx_contracturl="https://contract/contracts/c1"))


def user(user_id="u1", username="alice", owned=()):
    return Mock(id=user_id, username=username, owned_datasets=list(owned))


def read(path):
    with open(path) as file:
        return file.read()


class TestPdcInput:

    async def test_request_without_known_credentials_is_a_401(self, tmp_path):
        pdc_input = PdcInput(tmp_path, [])
        with pytest.raises(HTTPException) as error:
            await pdc_input.run()
        assert (error.value.status_code, error.value.detail) == (401, "No valid credentials found in headers")

    async def test_json_input_creates_a_dataset_for_the_user(self, tmp_path):
        alice = user()
        pdc_input = PdcInput(tmp_path, [alice])
        result = await pdc_input.run()

        path = os.path.join(pdc_input.folder(alice), "c1_1700000000.5.json")
        assert result == {
            "data": {"a": 1}, "path": "user_datasets", "contract_id": "c1", "provider_name": "Provider",
            "authenticated_users": 1,
            "user_datasets": [{"user": "alice", "dataset_id": "new-alice", "auth_method": "m2m_credentials",
                               "credentials_count": 1, "filepath": path}],
        }
        assert json.loads(read(path)) == {"a": 1}
        dataset, owner = pdc_input.add_connection.await_args.args
        assert owner is alice
        assert (dataset.name, dataset.type, dataset.folder, dataset.filePath, dataset.inputType, dataset.ifExist) == (
            "Provider_c1", "file", pdc_input.folder(alice), path, "file", "replace")
        pdc_input.fetch_contract.assert_called_once_with("https://contract/contracts/c1")

    async def test_dataset_without_provider_name_is_named_after_the_contract(self, tmp_path):
        pdc_input = PdcInput(tmp_path, [user()])
        pdc_input.provider_name = None
        await pdc_input.run()
        assert pdc_input.add_connection.await_args.args[0].name == "c1"

    @pytest.mark.parametrize("content_type, body, extension, data, written", [
        ("application/x-www-form-urlencoded", b"<a>1</a>", ".xml", "<a>1</a>", "<a>1</a>"),
        ("text/plain", b"hello", ".txt", "hello", "hello"),
        (None, b"hello", ".txt", "hello", "hello"),
        ("application/json; charset=utf-8", b'{"a": 1}', ".txt", '{"a": 1}', '{"a": 1}'),
    ])
    async def test_other_content_types_are_written_as_received(self, tmp_path, content_type, body, extension, data,
                                                               written):
        alice = user()
        pdc_input = PdcInput(tmp_path, [alice], content_type, body)
        result = await pdc_input.run()
        assert result["data"] == data
        assert read(os.path.join(pdc_input.folder(alice), f"c1_1700000000.5{extension}")) == written

    async def test_existing_dataset_in_append_mode_receives_the_data(self, tmp_path):
        alice = user(owned=["other", "broken", "existing"])
        pdc_input = PdcInput(tmp_path, [alice])
        pdc_input.datasets["other"] = PTXDataset.model_construct(id="other", type="ptx", name="Provider_c1")
        pdc_input.datasets["broken"] = RuntimeError("no access")
        existing = pdc_input.existing(alice, if_exist="append", content='[{"a": 0}]')
        result = await pdc_input.run()

        assert json.loads(read(existing.filePath)) == [{"a": 0}, {"a": 1}]
        assert os.listdir(pdc_input.folder(alice)) == ["previous.json"]
        assert result["user_datasets"][0]["dataset_id"] == "existing"
        assert result["user_datasets"][0]["filepath"] == existing.filePath
        pdc_input.add_connection.assert_not_awaited()
        pdc_input.edit_dataset.assert_not_awaited()

    async def test_existing_dataset_in_replace_mode_gets_a_new_file(self, tmp_path):
        alice = user(owned=["existing"])
        pdc_input = PdcInput(tmp_path, [alice])
        existing = pdc_input.existing(alice, content='{"a": 0}')
        result = await pdc_input.run()

        path = os.path.join(pdc_input.folder(alice), "c1_1700000000.5.json")
        assert os.listdir(pdc_input.folder(alice)) == ["c1_1700000000.5.json"]
        assert json.loads(read(path)) == {"a": 1}
        assert (existing.filePath, existing.ifExist) == (path, "replace")
        pdc_input.edit_dataset.assert_awaited_once_with(existing, alice)
        pdc_input.add_connection.assert_not_awaited()
        assert result["user_datasets"][0]["dataset_id"] == "existing"

    async def test_append_mode_without_file_gets_a_new_file(self, tmp_path):
        alice = user(owned=["existing"])
        pdc_input = PdcInput(tmp_path, [alice])
        existing = pdc_input.existing(alice, if_exist="append")
        await pdc_input.run()
        assert existing.filePath == os.path.join(pdc_input.folder(alice), "c1_1700000000.5.json")
        assert existing.ifExist == "replace"
        pdc_input.edit_dataset.assert_awaited_once()

    @pytest.mark.parametrize("values", [{"name": "Another name"}, {"folder": "/somewhere/else"}])
    async def test_dataset_with_another_name_or_folder_is_not_reused(self, tmp_path, values):
        alice = user(owned=["existing"])
        pdc_input = PdcInput(tmp_path, [alice])
        pdc_input.existing(alice, content='{"a": 0}', **values)
        result = await pdc_input.run()
        pdc_input.add_connection.assert_awaited_once()
        assert result["user_datasets"][0]["dataset_id"] == "new-alice"

    async def test_failure_for_one_user_does_not_stop_the_others(self, tmp_path):
        alice, bob = user("u1", "alice"), user("u2", "bob")
        pdc_input = PdcInput(tmp_path, [alice, bob])

        async def add_connection(dataset, owner):
            if owner is alice:
                raise RuntimeError("database down")
            dataset.id = "new-bob"

        pdc_input.add_connection.side_effect = add_connection
        result = await pdc_input.run()
        assert result["authenticated_users"] == 2
        assert [entry["user"] for entry in result["user_datasets"]] == ["bob"]
