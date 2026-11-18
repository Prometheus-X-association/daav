import asyncio
from typing import Tuple

import requests

from app.models.interface.pdc_chain_interface import PdcChainResponse


class PdcChainMixin:
    """Service chain steps shared by the output nodes that answer a PDC service chain.

    The node provides datasetService, which holds the headers of the running chain.
    """

    def _chain_ids(self) -> Tuple[str, str]:
        """Chain and target identifiers of the running service chain, empty outside a chain."""
        chain_headers = self.datasetService.pdcChainHeaders
        if chain_headers is None:
            return '', ''
        return chain_headers.x_ptx_service_chain_id, chain_headers.x_ptx_target_id

    async def _resume_chain(self, dataset, pdc_response: PdcChainResponse) -> None:
        """Send the response to the connector so that the service chain goes on; nothing outside a chain."""
        if self.datasetService.pdcChainHeaders is None:
            return
        url = f"{dataset.url}/service-chain/resume"
        headers = {
            "Content-Type": "application/json"
        }
        await asyncio.to_thread(requests.post, url, headers=headers, json=pdc_response.model_dump())
