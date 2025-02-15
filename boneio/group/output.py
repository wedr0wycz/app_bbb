"""Cover module."""
from __future__ import annotations
import logging
import asyncio
from typing import List

from boneio.const import COVER, SWITCH, ON, OFF
from boneio.relay.basic import BasicRelay

_LOGGER = logging.getLogger(__name__)


class OutputGroup(BasicRelay):
    """Cover class of boneIO"""

    def __init__(
        self,
        members: List[BasicRelay],
        output_type: str = SWITCH,
        restored_state: bool = True,
        **kwargs,
    ) -> None:
        """Initialize cover class."""
        self._loop = asyncio.get_event_loop()
        super().__init__(
            **kwargs, output_type=output_type, restored_state=restored_state, topic_type="group"
        )
        self._group_members = [x for x in members if x.output_type != COVER]
        self._timer_handle = None
        for member in self._group_members:
            self._event_bus.add_output_listener(member.id, self.event_listener)

    async def event_listener(self, relay_id=None) -> None:
        """Listen for events called by children relays."""
        state = OFF
        for x in self._group_members:
            if x.state == ON:
                state = ON
                break
        if state != self._state or not relay_id:
            self._state = state
            self._loop.call_soon_threadsafe(self.send_state)

    def turn_on(self) -> None:
        """Call turn on action."""
        for x in self._group_members:
            asyncio.create_task(x.async_turn_on())

    def turn_off(self) -> None:
        """Call turn off action."""
        for x in self._group_members:
            asyncio.create_task(x.async_turn_off())

    def toggle(self) -> None:
        """Toggle group."""
        _LOGGER.debug("Toggle relay.")
        if self._state == ON:
            self.turn_off()
        else:
            self.turn_on()

    def send_state(self) -> None:
        """Send state to Mqtt on action."""
        self._send_message(topic=self._send_topic, payload=self.payload(), retain=True)
