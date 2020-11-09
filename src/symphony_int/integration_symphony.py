# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

import asyncio
import time
import json

from dataclasses import dataclass

from dazl import create, exercise
from dazl.model.core import ContractData

from daml_dit_api import \
    IntegrationEnvironment, IntegrationEvents

from daml_dit_if.main.web import json_response

from sym_api_client_python.clients.sym_bot_client import SymBotClient
from sym_api_client_python.listeners.im_listener import IMListener
from sym_api_client_python.listeners.elements_listener import ElementsActionListener
from sym_api_client_python.processors.sym_message_parser import SymMessageParser
from sym_api_client_python.processors.sym_elements_parser import SymElementsParser

from sym_api_client_python.listeners.connection_listener import ConnectionListener

from .config import SymObjectConfig
from .rsa_string_auth import SymBotRSAStringAuth

LOG = logging.getLogger('integration')

class SYMPHONY:
    InboundDirectMessage = 'SymphonyIntegration.InboundDirectMessage.InboundDirectMessage'
    InboundElementAction = 'SymphonyIntegration.InboundElementAction.InboundElementAction'
    OutboundMessage = 'SymphonyIntegration.OutboundMessage:OutboundMessage'
    UserStream = 'Symphony:UserStream'


@dataclass
class IntegrationSymphonyEnv(IntegrationEnvironment):
    host : str
    port : int
    private_key : str
    bot_username : str
    bot_email : str
    token_refresh_period : int
    interval : int


def integration_symphony_main(
        env: 'IntegrationSymphonyEnv',
        events: 'IntegrationEvents'):

    inbound_queue = asyncio.Queue()

    async def dequeue_inbound() -> dict:
        msg = await inbound_queue.get()
        LOG.info(f"Dequeued inbound message: {msg}")
        return msg

    configure = SymObjectConfig(
            env.host, env.port, env.bot_username, env.bot_email, env.token_refresh_period)

    auth = SymBotRSAStringAuth(configure, env.private_key)
            # getKey()) # env.private_key)
    auth.authenticate()

    bot_client = SymBotClient(auth, configure)

    # Initialize datafeed service
    datafeed_event_service = bot_client.get_async_datafeed_event_service()

    datafeed_event_service.add_im_listener(IMListenerImpl(env, inbound_queue))
    datafeed_event_service.add_elements_listener(ElementsListenerImpl(bot_client, env, inbound_queue))
    datafeed_event_service.add_connection_listener(ConnectionListenerImpl(bot_client))

    @events.time.periodic_interval(env.interval)
    async def process_inbound_messages():
        if not inbound_queue.empty():
            LOG.info(f"Will process {inbound_queue.qsize()} messages...")

        commands = []
        while not inbound_queue.empty():  # drain the queue
            msg = await dequeue_inbound()
            commands.append(create(msg['type'], msg['payload']))

        return commands

    @events.ledger.contract_created(
        SYMPHONY.OutboundMessage)
    async def on_outbound_message_created(event):
        LOG.info('symphony send message - created: %r', event)
        message = event.cdata['messageText']
        stream_id = event.cdata['symphonyStreamId']
        bot_client.get_message_client().send_msg(stream_id, dict(message=f'<messageML>{message}</messageML>'))
        return [exercise(event.cid, 'Archive')]


    return datafeed_event_service.start_datafeed()

class IMListenerImpl(IMListener):
    def __init__(self, env: IntegrationSymphonyEnv, inbound_queue):
        self.env = env
        self.inbound_queue = inbound_queue
        self.message_parser = SymMessageParser()

    async def on_im_message(self, im_message):
        logging.debug('IM Message Received')

        msg_text = self.message_parser.get_text(im_message)
        first_name = self.message_parser.get_im_first_name(im_message)
        stream_id = self.message_parser.get_stream_id(im_message)
        username = im_message['user']['username']

        msg_data = {
            'type': SYMPHONY.InboundDirectMessage,
            'payload': {
                'integrationParty': self.env.party,
                'symphonyChannel': first_name,
                'symphonyUser': username,
                'symphonyStreamId': stream_id,
                'messageText': msg_text
            }
        }
        await self.inbound_queue.put(msg_data)

    async def on_im_created(self, im_created):
        logging.debug('IM created %s', im_created)

class ElementsListenerImpl(ElementsActionListener):
    def __init__(self, sym_bot_client: SymBotClient, env: IntegrationSymphonyEnv, inbound_queue):
        self.bot_client = sym_bot_client
        self.env = env
        self.inbound_queue = inbound_queue

    async def on_elements_action(self, action):
        stream_type = self.bot_client.get_stream_client().stream_info_v2(SymElementsParser().get_stream_id(action))
        if stream_type['streamType']['type'] == 'IM':
            form_id = SymElementsParser().get_form_id(action)
            stream_id = SymElementsParser().get_stream_id(action)
            button_action = SymElementsParser().get_action(action)
            form_contents = SymElementsParser().get_form_values(action)
            username = action['initiator']['user']['email']
            msg_data = {
                'type': SYMPHONY.InboundElementAction,
                'payload': {
                    'integrationParty': self.env.party,
                    'symphonyUser': username,
                    'symphonyStreamId': stream_id,
                    'formId': form_id,
                    'action': button_action,
                    'formJSON' : json.dumps(form_contents)
                }
            }
            await self.inbound_queue.put(msg_data)

class ConnectionListenerImpl(ConnectionListener):
    def __init__(self, sym_bot_client):
        self.bot_client = sym_bot_client

    async def on_connection_accepted(self, connection):
        logging.debug('Connection Request Accepted: %s', connection)

    async def on_connection_requested(self, connection):
        logging.debug('Connection Request Received: %s', connection)

