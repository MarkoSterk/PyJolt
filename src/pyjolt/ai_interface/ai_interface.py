"""
AI interface for PyJolt app
Makes connecting to LLM's easy
"""
from abc import ABC, abstractmethod
import inspect
from functools import wraps
from typing import (List, Dict, Any, Optional, get_type_hints, Callable)
import docstring_parser
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall

from ..pyjolt import PyJolt, Request, HttpStatus, Response
from ..utilities import run_sync_or_async
from ..exceptions import BaseHttpException
from ..base_extension import BaseExtension

class ChatContextNotFound(BaseHttpException):

    def __init__(self, msg: str, status_code: int|HttpStatus = HttpStatus.NOT_FOUND):
        super().__init__(msg, status_code=status_code)
        if isinstance(status_code, HttpStatus):
            status_code = status_code.value
        self.status_code = status_code

class FailedToRunAiToolMethod(BaseHttpException):

    def __init__(self, msg: str,
                 method_name: str,
                 *args,
                 status_code: int|HttpStatus = HttpStatus.UNPROCESSABLE_ENTITY,
                 **kwargs):
        super().__init__(msg, status_code=status_code)
        if isinstance(status_code, HttpStatus):
            status_code = status_code.value
        self.status_code = status_code
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs

class AiInterface(BaseExtension, ABC):
    """
    Main AI interface
    """
    _DEFAULT_CONFIGS = {
        "timeout": 30,
        "temperature": 1.0,
        "model": "gpt-3.5-turbo",
        "api_base_url": "https://api.openai.com/v1",
        "response_format": {
            "type": "json_object"
        },
        "tool_choice": False,
        "max_retries": 0
    }

    def __init__(self, variable_prefix: str = ""):
        """
        Extension init method
        """
        self._app: PyJolt = None
        self._api_key: str = None
        self._api_base_url: str = None
        self._organization_id: str = None
        self._project_id: str = None
        self._variable_prefix: str = variable_prefix
        self._timeout: int = None
        self._model: str = None
        self._temperature: float = None
        self._response_format: dict[str, str] = None
        self._tool_choice = False
        self._max_retries: int = None
        self._tools: list = []
        self._tools_mapping: dict[str, Callable] = {}
        self._chat_session_loader: Callable = None
        self._provider_methods: dict[str, Callable] = {}
        self._chat_session_model_type = None
        self._chat_context_name: str = "chat_context"
        
        self._get_tools()

    def init_app(self, app: PyJolt):
        """
        Initilizer method for extension
        """
        self._app = app
        self._api_key = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_API_KEY",
                                           None)
        self._api_base_url = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_API_BASE_URL",
                                                self._DEFAULT_CONFIGS["api_base_url"])
        self._organization_id = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_ORGANIZATION_ID",
                                                    None)
        self._project_id = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_PROJECT_ID",
                                                    None)
        self._timeout = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TIMEOUT",
                                           self._DEFAULT_CONFIGS["timeout"])
        self._model = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_MODEL",
                                         self._DEFAULT_CONFIGS["model"])
        self._temperature = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TEMPERATURE",
                                               self._DEFAULT_CONFIGS["temperature"])
        self._response_format = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_RESPONSE_FORMAT",
                                                   self._DEFAULT_CONFIGS["response_format"])
        self._tool_choice = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TOOL_CHOICE",
                                               self._DEFAULT_CONFIGS["tool_choice"])
        self._max_retries = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_MAX_RETRIES",
                                               self._DEFAULT_CONFIGS["max_retries"])
        self._chat_context_name = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_CHAT_CONTEXT_NAME",
                                                    self._chat_context_name)

        self._app.add_extension(self)
    
    @property
    def configs(self) -> dict[str, str|int|float|dict|None]:
        """
        Returns default configs object with env. var. or extension defaults
        """
        return {
            "api_key": self._api_key,
            "api_base_url": self._api_base_url,
            "organization_id": self._organization_id,
            "project_id": self._project_id,
            "timeout": self._timeout,
            "model": self._model,
            "temperature": self._temperature,
            "response_format": self._response_format,
            "tool_choice": self._tool_choice,
            "max_retries": self._max_retries
        }

    async def provider(self,
                    messages: List[Dict[str, str]],
                    **kwargs) -> tuple[str|None, list[ChatCompletionMessageToolCall]|None, ChatCompletion|None]:
        """
        Default provider method. Uses AsyncOpenAI from the openai package
        """

        # Build request
        api_key = kwargs.get("api_key", self._api_key)
        organization = kwargs.get("organization", self._organization_id)
        project = kwargs.get("project", self._project_id)
        timeout = kwargs.get("timeout", self._timeout)
        base_url = kwargs.get("api_base_url", self._api_base_url)
        max_retries = kwargs.get("max_retries", self._max_retries)

        client: AsyncOpenAI = AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            project=project,
            timeout=timeout,
            base_url=base_url,
            max_retries=max_retries
        )

        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        response_format = kwargs.get("response_format", self._response_format)

        configs: dict = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "response_format": response_format,
        }
        if kwargs.get("use_tools", False):
            configs["tools"] = self._tools

        chat: ChatCompletion = await client.chat.completions.create(**configs)
        tool_calls = chat.choices[0].message.tool_calls or None
        assistant_message_content = chat.choices[0].message.content or None
        return assistant_message_content, tool_calls, chat

    async def create_chat_completion(self,
        messages: List[Dict[str, str]],
        **kwargs) -> tuple[str|None, list[ChatCompletionMessageToolCall]|None, ChatCompletion|None]:
        """
        Makes prompt with chosen provider method.
        Default is the default_provider method which is OpenAI compatible.

        :param stream: bool = False
        :returns chat_completion:
        """
        ##if default method is selected
        return await self.provider(messages, **kwargs)
        
    
    async def envoke_ai_tool(self, tool_name, *args, **kwargs) -> Any:
        """
        Runs a registered AI tool method
        """
        tool_method: Optional[Callable] = self._tools_mapping.get(tool_name, None)
        if tool_method is None:
            raise ValueError(f"Tool method named {tool_name} is not registered with the AI interface")
        try:
            return await run_sync_or_async(tool_method, *args, **kwargs)
        except Exception as exc:
            raise FailedToRunAiToolMethod(f"Failed to run AI tool {tool_name}", *args, **kwargs) from exc

    def build_function_schema(self, func: Callable,
                                    func_name: Optional[str] = None,
                                     description: Optional[str] = None) -> dict[str, any]:
        """
        Automatically builds an OpenAI function schema from a Python function.
        Assumes docstring and type hints follow some basic conventions.
        """
        # Parse the docstring
        doc = docstring_parser.parse(func.__doc__ or "")
        func_description = description or doc.short_description or ""

        # Build the skeleton
        schema: dict[str, Any] = {
            "type": "function",
            "function": {
                "name": func_name or func.__name__,
                "description": func_description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                }
            }
        }

        # Collect parameter info
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        for param_name, param in sig.parameters.items():
            # Derive param type from hints
            param_type = hints.get(param_name, str)
            if param_type is str:
                schema_type = "string"
            elif param_type in [int, float]:
                schema_type = "number"
            elif param_type is bool:
                schema_type = "boolean"
            else:
                schema_type = "string"

            param_desc: str|None = ""
            for doc_param in doc.params:
                if doc_param.arg_name == param_name:
                    param_desc = doc_param.description
                    break

            schema["function"]["parameters"]["properties"][param_name] = {
                "type": schema_type,
                "description": param_desc,
            }
            #If no default value is detected, the parameter is required
            if param.default is inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)
        return schema

    @abstractmethod
    async def chat_context_loader(self, req: Request, *args: Any, **kwargs: Any) -> Optional[Any]:
        """Should load and return a chat session object (ie db model) or none"""

    @property
    def chat_context_name(self) -> str:
        return self._chat_context_name

    @property
    def with_chat_context(self) -> Callable:
        """
        Decorator for injecting chat session to route handler.
        Uses the chat session loader method added with the
        @chat_context_loader decorator.

        Injects the chat context object as a keyword argument
        """
        interface: AiInterface = self
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(self, *args, **kwargs) -> "Response":
                req: Request = args[0]
                if not isinstance(req, Request):
                    raise ValueError("Missing Request object at @with_chat_context decorator. The request object"
                                     " must be the first argument of the route handler. Please check if you have "
                                     "changed the argument sequence.")
                chat_context = await run_sync_or_async(interface.chat_context_loader, req)
                if chat_context is None:
                    raise ChatContextNotFound("Chat session not found")
                kwargs[interface.chat_context_name] = chat_context
                return await run_sync_or_async(func, self, *args, **kwargs)
            return wrapper
        return decorator

    def _get_tools(self):
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue

            is_tool = getattr(method, "__ai_tool", None) or None
            if not is_tool:
                continue
            self._tools.append(self.build_function_schema(method, is_tool["name"],
                                                          is_tool["description"]))
            self._tools_mapping[is_tool["name"]] = method

def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator for adding a method as a tool to the Ai interface
    """
    def decorator(func: Callable):
        """
        Marks method to as ai interface tool
        """
        setattr(func, "__ai_tool", {
            "name": name or func.__name__,
            "description": description or func.__doc__
        })
        return func
    return decorator
