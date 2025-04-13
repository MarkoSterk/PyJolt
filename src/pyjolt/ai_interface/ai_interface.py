"""
AI interface for PyJolt app
Makes connecting to LLM's easy
"""
import inspect
from functools import wraps
from typing import (List, Dict, Any, get_type_hints,
                    Union, AsyncIterator, Callable)
import docstring_parser
from openai import AsyncOpenAI

from ..pyjolt import PyJolt, Request
from ..utilities import run_sync_or_async

class AiInterface:
    """
    Main AI interface
    """

    timeout: int = 30 #timeout in seconds
    temperature: float = 1.0
    model: str = "gpt-3.5-turbo"
    api_base_url: str = "https://api.openai.com/v1"
    response_format: dict[str, str] = { "type": "json_object" }
    tool_choice = None
    max_retries: int = 0

    def __init__(self, app: PyJolt = None, variable_prefix: str = ""):
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
        self._tool_choice = None
        self._max_retries: int = None
        self._tools: dict[str, dict[str, any]] = []
        self._tools_mapping: dict[str, Callable] = {}
        self._chat_session_loader: Callable = None
        self._provider_methods: dict[str, Callable] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: PyJolt):
        """
        Initilizer method for extension
        """
        self._app = app
        self._api_key = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_API_KEY",
                                           None)
        self._api_base_url = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_API_BASE_URL",
                                                self.api_base_url)
        self._organization_id = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_ORGANIZATION_ID",
                                                    None)
        self._project_id = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_PROJECT_ID",
                                                    None)
        self._timeout = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TIMEOUT",
                                           self.timeout)
        self._model = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_MODEL",
                                         self.model)
        self._temperature = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TEMPERATURE",
                                               self.temperature)
        self._response_format = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_RESPONSE_FORMAT")
        self._tool_choice = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_TOOL_CHOICE",
                                               self._tool_choice)
        self._max_retries = self._app.get_conf(f"{self._variable_prefix}AI_INTERFACE_MAX_RETRIES",
                                               self.max_retries)

        self._app.add_extension(self)
    
    @property
    def default_configs(self) -> dict[str, str|int|float|dict]:
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

    async def default_provider(self,
                        messages: List[Dict[str, str]],
                        **kwargs) -> tuple[str, list, any]:
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
        if kwargs.get("use_tools", True):
            configs["tools"] = self._tools

        chat = await client.chat.completions.create(**configs)
        tool_calls = chat.choices[0].message.tool_calls or None
        assistant_message_content = chat.choices[0].message.content or None
        return assistant_message_content, tool_calls, chat

    async def create_chat_completion(self,
        messages: List[Dict[str, str]],
        provider: str = "default",
        stream: bool = False,
        **kwargs) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Makes prompt with chosen provider method.
        Default is the default_provider method which is OpenAI compatible.

        :param provider: str = "default"
        :param stream: bool = False
        :returns chat_completion:
        """
        provider_name: str = f"{provider}"
        if stream:
            provider_name = f"{provider_name}_stream"
        ##if default method is selected
        provider_name = f"{provider_name}_provider"
        provider: Callable = getattr(self, provider_name, None)
        if provider is not None:
            return await provider(messages, **kwargs)
        #if default method is not selected it tries to use one of the provided methods
        provider_method: Callable = self._provider_methods.get(provider_name, None)
        if provider_method is None:
            raise ValueError(f"Ai_interface provider method with name {provider.split("_")[0]} (stream={stream}) does not exist."
                             "Please use existing methods or add a new one.")
        return await provider_method(self, messages, **kwargs)
    
    async def envoke_ai_tool(self, tool_name, *args, **kwargs):
        """
        Runs a registered AI tool method
        """
        tool_method: Callable = self._tools_mapping.get(tool_name, None)
        if tool_method is None:
            raise ValueError(f"Tool method named {tool_name} is not registered with the AI interface")
        return await run_sync_or_async(tool_method, *args, **kwargs)

    def ai_interface_provider(self, provider_name: str = None, stream: bool = False):
        """
        Decorator for adding ai interface provider methods.
        Sets the decorated function as an instance method on the ai_interface instance
        with the name {provider_name}_provider.

        If stream = True, the provider is saved with the name: {provider_name}_stream_provider

        The decorated method should be an async method to avoid blocking the event loop
        during LLM calls. Use of the httpx package is recommended.

        :param provider_name: str - name of the provider method. 
                            Default is the func.__name__ attribute

        The decorated method should accept the "self" argument as the first argument
        and messages as the second. There can also be any number of
        keyword arguments.
        """
        def decorator(func: Callable):
            """
            Adds provider to Ai interface instance
            """
            nonlocal provider_name, stream
            if provider_name is None:
                provider_name = func.__name__
            if stream:
                provider_name = f"{provider_name}_stream"
            self._provider_methods[f"{provider_name}_provider"] = func
        return decorator

    def build_function_schema(self, func: Callable,
                                    func_name: str = None,
                                     description: str = None) -> dict[str, any]:
        """
        Automatically builds an OpenAI function schema from a Python function.
        Assumes docstring and type hints follow some basic conventions.
        """
        # Parse the docstring
        doc = docstring_parser.parse(func.__doc__ or "")
        func_description = description or doc.short_description or ""

        # Build the skeleton
        schema = {
            "type": "function",
            "function": {
                "name": func_name or func.__name__,
                "description": func_description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            }
        }

        # Collect parameter info
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        for param_name, param in sig.parameters.items():
            # Derive param type from hints
            param_type = hints.get(param_name, str)  # default to str if not annotated
            if param_type is str:
                schema_type = "string"
            elif param_type in [int, float]:
                schema_type = "number"
            elif param_type is bool:
                schema_type = "boolean"
            else:
                schema_type = "string"

            param_desc = ""
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

    def ai_tool(self, name: str = None, description: str = None):
        """
        Decorator for adding a method as a tool to the Ai interface
        """
        def decorator(func: Callable):
            """
            Adds method to ai interface
            Creates a schema for the function definition
            """
            nonlocal name, description
            if name is None:
                name = func.__name__
            self._tools.append(self.build_function_schema(func, name, description))
            self._tools_mapping[name] = func
            return func
        return decorator

    @property
    def chat_session_loader(self):
        """
        Adds a chat session loader to the ai interface.
        Needed for injecting chat sessions into route handlers
        with the @with_chat_session decorator.

        The decorated method will receive the Request object as the single
        argument.
        """
        def decorator(func: Callable):
            self._chat_session_loader = func
            return func
        return decorator

    @property
    def with_chat_session(self):
        """
        Decorator for injecting chat session to route handler.
        Uses the chat session loader method added with the
        @chat_session_loader decorator.

        Injects the chat session object as a keyword argument named "chat_session"
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                req: Request = args[0]
                if not isinstance(req, Request):
                    raise ValueError("Missing Request object at @with_chat_session decorator. The request object"
                                     " must be the first argument of the route handler. Please check if you have "
                                     "changed the argument sequence.")
                chat_session = await run_sync_or_async(self._chat_session_loader, req)
                kwargs["chat_session"] = chat_session
                return await func(*args, **kwargs)
            return wrapper
        return decorator
