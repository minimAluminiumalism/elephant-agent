from __future__ import annotations

import asyncio
import unittest

from packages.gateway_core import InboundSequencer


class InboundSequencerTest(unittest.TestCase):
    def test_same_key_runs_in_fifo_order_and_cleans_up(self) -> None:
        async def scenario() -> None:
            sequencer = InboundSequencer()
            first_entered = asyncio.Event()
            release_first = asyncio.Event()
            second_entered = asyncio.Event()
            order: list[str] = []
            key = InboundSequencer.key_for(account_id="acct", conversation_id="conv")

            async def run_first() -> None:
                async def critical_section() -> None:
                    order.append("first:start")
                    first_entered.set()
                    await release_first.wait()
                    order.append("first:end")

                await sequencer.run_serialized(key, critical_section)

            async def run_second() -> None:
                async def critical_section() -> None:
                    second_entered.set()
                    order.append("second")

                await sequencer.run_serialized(key, critical_section)

            first_task = asyncio.create_task(run_first())
            second_task = asyncio.create_task(run_second())

            await first_entered.wait()
            await asyncio.sleep(0)
            self.assertFalse(second_entered.is_set())

            release_first.set()
            await asyncio.gather(first_task, second_task)

            self.assertEqual(order, ["first:start", "first:end", "second"])
            self.assertEqual(sequencer.tracked_key_count, 0)

        asyncio.run(scenario())

    def test_different_keys_can_progress_independently(self) -> None:
        async def scenario() -> None:
            sequencer = InboundSequencer()
            first_entered = asyncio.Event()
            second_entered = asyncio.Event()
            release_first = asyncio.Event()
            order: list[str] = []

            async def run_first() -> None:
                async def critical_section() -> None:
                    order.append("first:start")
                    first_entered.set()
                    await release_first.wait()
                    order.append("first:end")

                await sequencer.run_serialized(
                    InboundSequencer.key_for(account_id="acct", conversation_id="conv-1"),
                    critical_section,
                )

            async def run_second() -> None:
                async def critical_section() -> None:
                    second_entered.set()
                    order.append("second")

                await sequencer.run_serialized(
                    InboundSequencer.key_for(account_id="acct", conversation_id="conv-2"),
                    critical_section,
                )

            first_task = asyncio.create_task(run_first())
            second_task = asyncio.create_task(run_second())

            await first_entered.wait()
            await second_entered.wait()
            self.assertEqual(order, ["first:start", "second"])

            release_first.set()
            await asyncio.gather(first_task, second_task)
            self.assertEqual(sequencer.tracked_key_count, 0)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
