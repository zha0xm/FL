"""Utility functions for mods."""


from client.typing import ClientAppCallable, Mod
from common import Context, Message


def make_ffn(ffn: ClientAppCallable, mods: list[Mod]) -> ClientAppCallable:
    """."""

    def wrap_ffn(_ffn: ClientAppCallable, _mod: Mod) -> ClientAppCallable:
        def new_ffn(message: Message, context: Context) -> Message:
            return _mod(message, context, _ffn)

        return new_ffn

    for mod in reversed(mods):
        ffn = wrap_ffn(ffn, mod)

    return ffn