import warnings

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except Exception:
    pass

warnings.filterwarnings(
    'ignore',
    message=r'The default value of `allowed_objects` will change in a future version.*',
    module=r'langgraph\.cache\.base',
)
