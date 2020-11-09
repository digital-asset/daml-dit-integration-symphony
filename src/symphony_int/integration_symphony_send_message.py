# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass

from dazl import exercise
from dazl.model.core import ContractData

from daml_dit_api import \
    IntegrationEnvironment, IntegrationEvents

from daml_dit_if.main.web import json_response

from sym_api_client_python.clients.sym_bot_client import SymBotClient

from .config import SymObjectConfig
from .rsa_string_auth import SymBotRSAStringAuth

LOG = logging.getLogger('integration')


@dataclass
class IntegrationSymphonySendMessageEnv(IntegrationEnvironment):
    host : str
    port : int
    private_key : str
    bot_username : str
    bot_email : str
    token_refresh_period : int


def integration_symphony_send_main(
        env: 'IntegrationSymphonySendMessageEnv',
        events: 'IntegrationEvents'):

    configure = SymObjectConfig(
            env.host, env.port,
            env.bot_username, env.bot_email, env.token_refresh_period)

    # config = configure._makeConfig(env.host, env.port, env.bot_username, env.bot_email, env.token_refresh_period)
    # configure._load_config(config) # getConfigDict())

    auth = SymBotRSAStringAuth(configure, env.private_key)
    auth.authenticate()

    bot_client = SymBotClient(auth, configure)

    @events.ledger.contract_created(
        'SymphonyIntegration.OutboundMessage:OutboundMessage')
    async def on_contract_created(event):
        LOG.info('symphony send message - created: %r', event)
        message = event.cdata['messageText']
        stream_id = event.cdata['symphonyStreamId']
        bot_client.get_message_client().send_msg(stream_id, dict(message=f'<messageML>{message}</messageML>'))
        # return []
        return [exercise(event.cid, 'Archive')]
