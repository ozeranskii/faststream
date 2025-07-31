import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from fast_depends.library.serializer import SerializerProto
from fast_depends.msgspec import MsgSpecSerializer
from fast_depends.pydantic import PydanticSerializer
from msgspec import Struct
from pydantic import BaseModel

from faststream._internal.broker.broker import BrokerUsecase
from faststream._internal.testing.broker import TestBroker
from faststream.confluent import (
    KafkaBroker as ConfluentBroker,
    TestKafkaBroker as TestConfluentBroker,
    TopicPartition,
)
from faststream.kafka import KafkaBroker, TestKafkaBroker
from faststream.nats import NatsBroker, TestNatsBroker
from faststream.rabbit import RabbitBroker, TestRabbitBroker
from faststream.redis import RedisBroker, TestRedisBroker


class PydanticMessage(BaseModel):
    r: str


class MsgspecMessage(Struct):
    r: str


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("broker_cls", "test_cls", "subscriber_params"),
    (
        pytest.param(RabbitBroker, TestRabbitBroker, (("test",), {}), id="rabbit"),
        pytest.param(RedisBroker, TestRedisBroker, (("test",), {}), id="redis"),
        pytest.param(KafkaBroker, TestKafkaBroker, (("test",), {}), id="kafka"),
        pytest.param(NatsBroker, TestNatsBroker, (("test",), {}), id="nats"),
        pytest.param(
            ConfluentBroker,
            TestConfluentBroker,
            (
                (),
                {
                    "partitions": [TopicPartition(topic="test", partition=0, offset=0)],
                    "auto_offset_reset": "earliest",
                },
            ),
            id="confluent",
        ),
    ),
)
@pytest.mark.parametrize(
    ("serializer", "message"),
    (
        pytest.param(MsgSpecSerializer(), MsgspecMessage(r="hello!"), id="msgspec"),
        pytest.param(PydanticSerializer(), PydanticMessage(r="hello!"), id="pydantic"),
        pytest.param(None, {"r": "hello!"}, id="default"),
    ),
)
class TestSerializer:
    async def test_publish(
        self,
        mock: MagicMock,
        broker_cls: type[BrokerUsecase[Any, Any]],
        test_cls: type[TestBroker[Any]],
        serializer: SerializerProto | None,
        subscriber_params: dict[str, Any],
        message: Any,
    ) -> None:
        broker = broker_cls(serializer=serializer)

        args, kwargs = subscriber_params

        @broker.subscriber(*args, **kwargs)
        async def handler(m: type(message)) -> None:
            mock(m)

        async with test_cls(broker) as br:
            await br.publish(message, "test")

        mock.assert_called_with(message)

    @pytest.mark.connected()
    async def test_publisher(
        self,
        mock: MagicMock,
        broker_cls: type[BrokerUsecase[Any, Any]],
        test_cls: type[TestBroker[Any]],
        serializer: type[SerializerProto],
        subscriber_params: dict[str, Any],
        message: Any,
    ) -> None:
        broker = broker_cls(serializer=serializer)
        publisher = broker.publisher("test")
        event = asyncio.Event()

        args, kwargs = subscriber_params

        @broker.subscriber(*args, **kwargs)
        async def handler(m: type(message)) -> None:
            mock(m)
            event.set()

        async with broker:
            await broker.start()
            await publisher.publish(message)
            await asyncio.wait((asyncio.create_task(event.wait()),), timeout=3)

        mock.assert_called_with(message)
