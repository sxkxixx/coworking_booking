from abc import abstractmethod, ABC

import fastapi_jsonrpc as jsonrpc


class AbstractRPCRouter(ABC):
    """Abstract JSON-RPC Router"""

    @abstractmethod
    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        """
        Register methods and returns jsonrpc.Entrypoint
        :return: jsonrpc.Entrypoint
        """
        raise NotImplementedError()
