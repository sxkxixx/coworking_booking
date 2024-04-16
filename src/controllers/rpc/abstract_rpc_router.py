from abc import abstractmethod, ABC

import fastapi_jsonrpc as jsonrpc


class AbstractRPCRouter(ABC):
    @abstractmethod
    def build_entrypoint(self) -> jsonrpc.Entrypoint:
        raise NotImplementedError()
