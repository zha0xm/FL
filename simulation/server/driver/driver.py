"""Driver (abstract base class)."""


from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Optional

from common import RecordSet, Message
from common.typing import Run


class Driver(ABC):
    """Abstract base Driver class for the ServerAppIo API."""

    @abstractmethod
    def set_run(self, run_id: int) -> None:
        """Request a run to the SuperLink with a given `run_id`.

        If a Run with the specified `run_id` exists, a local Run
        object will be created. It enables further functionality
        in the driver, such as sending `Messages`.

        Parameters
        ----------
        run_id : int
            The `run_id` of the Run this Driver object operates in.
        """

    @property
    @abstractmethod
    def run(self) -> Run:
        """Run information."""

    @abstractmethod
    def create_message(  # pylint: disable=too-many-arguments,R0917
        self,
        content: RecordSet,
        message_type: str,
        dst_node_id: int,
        group_id: str,
        ttl: Optional[float] = None,
    ) -> Message:
        """Create a new message with specified parameters.

        This method constructs a new `Message` with given content and metadata.
        The `run_id` and `src_node_id` will be set automatically.

        Parameters
        ----------
        content : RecordSet
            The content for the new message. This holds records that are to be sent
            to the destination node.
        message_type : str
            The type of the message, defining the action to be executed on
            the receiving end.
        dst_node_id : int
            The ID of the destination node to which the message is being sent.
        group_id : str
            The ID of the group to which this message is associated. In some settings,
            this is used as the FL round.
        ttl : Optional[float] (default: None)
            Time-to-live for the round trip of this message, i.e., the time from sending
            this message to receiving a reply. It specifies in seconds the duration for
            which the message and its potential reply are considered valid. If unset,
            the default TTL (i.e., `common.DEFAULT_TTL`) will be used.

        Returns
        -------
        message : Message
            A new `Message` instance with the specified content and metadata.
        """

    @abstractmethod
    def get_node_ids(self) -> Iterable[int]:
        """Get node IDs."""

    @abstractmethod
    def push_messages(self, messages: Iterable[Message]) -> Iterable[str]:
        """Push messages to specified node IDs.

        This method takes an iterable of messages and sends each message
        to the node specified in `dst_node_id`.

        Parameters
        ----------
        messages : Iterable[Message]
            An iterable of messages to be sent.

        Returns
        -------
        message_ids : Iterable[str]
            An iterable of IDs for the messages that were sent, which can be used
            to pull replies.
        """

    @abstractmethod
    def pull_messages(self, message_ids: Iterable[str]) -> Iterable[Message]:
        """Pull messages based on message IDs.

        This method is used to collect messages from the SuperLink
        that correspond to a set of given message IDs.

        Parameters
        ----------
        message_ids : Iterable[str]
            An iterable of message IDs for which reply messages are to be retrieved.

        Returns
        -------
        messages : Iterable[Message]
            An iterable of messages received.
        """

    @abstractmethod
    def send_and_receive(
        self,
        messages: Iterable[Message],
        *,
        timeout: Optional[float] = None,
    ) -> Iterable[Message]:
        """Push messages to specified node IDs and pull the reply messages.

        This method sends a list of messages to their destination node IDs and then
        waits for the replies. It continues to pull replies until either all
        replies are received or the specified timeout duration is exceeded.

        Parameters
        ----------
        messages : Iterable[Message]
            An iterable of messages to be sent.
        timeout : Optional[float] (default: None)
            The timeout duration in seconds. If specified, the method will wait for
            replies for this duration. If `None`, there is no time limit and the method
            will wait until replies for all messages are received.

        Returns
        -------
        replies : Iterable[Message]
            An iterable of reply messages received from the SuperLink.

        Notes
        -----
        This method uses `push_messages` to send the messages and `pull_messages`
        to collect the replies. If `timeout` is set, the method may not return
        replies for all sent messages. A message remains valid until its TTL,
        which is not affected by `timeout`.
        """