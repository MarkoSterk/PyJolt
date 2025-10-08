<p align="center">
  <img src="https://raw.githubusercontent.com/MarkoSterk/PyJolt/refs/heads/main/src/pyjolt/graphics/pyjolt_logo.png" alt="PyJolt Logo" width="200">
</p>

# PyJolt - async first python web framework

This framework is in its alpha stage and will probably see some major changes/improvements until it reaches
the beta stage for testing. Any eager tinkerers are invited to test the framework in its alpha stage and provide feedback.

## Getting started

### From PyPi with uv or pip

In your project folder
```
uv init
uv add pyjolt
```
or with pip
```
pip install pyjolt
```
We strongly recommend using uv for dependency management.

The above command will install pyjolt with basic dependencies. For some subpackages you will need additional dependencies. Options are:

**Caching**
```
uv add "pyjolt[cache]"
```

**Scheduler**
```
uv add "pyjolt[scheduler]"
```

**AI interface** (experimental)
```
uv add "pyjolt[ai_interface]"
```

**Full install**
```
uv add "pyjolt[full]"
```

##Getting started with project template

```
uv run pyjolt new-project
```

or with pip (don't forget to activate the virtual environment)
```
pipx pyjolt new-project
```

This will create a template project structure which you can use to get started.

## Blank start

If you wish to start without the template you can do that ofcourse. However, we recommend you have a look at the template structure to see how to organize your project. There is also an example project in the "examples/dev" folder of this GitHub repo where you can see the app structure and recommended patterns.

A minimum app example would be:

```
#app/__init__.py <-- in the app folder

from app.configs import Config
from pyjolt import PyJolt, app, on_shutdown, on_startup

@app(__name__, configs = Config)
class Application(PyJolt):
    pass
```

and the configuration object is:

```
#app/configs.py <-- in the app folder

import os
from pyjolt import BaseConfig

class Config(BaseConfig): #must inherit from BaseConfig
    """Config class"""
    APP_NAME: str = "Test app"
    VERSION: str = "1.0"
    SECRET_KEY: str = "some-super-secret-key" #change for a secure random string
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = True
```

Available configuration options of the application are:

```
APP_NAME: str = Field(description="Human-readable name of the app")
VERSION: str = Field(description="Application version")
BASE_PATH: str #base path of app. os.path.dirname(__file__) in the configs.py file is the usual value

# required for Authentication extension
SECRET_KEY: Optional[str]

# optionals with sensible defaults
DEBUG: Optional[bool] = True
HOST: Optional[str] = "localhost"
TEMPLATES_DIR: Optional[str] = "/templates"
STATIC_DIR: Optional[str] = "/static"
STATIC_URL: Optional[str] = "/static"
TEMPLATES_STRICT: Optional[bool] = True
STRICT_SLASHES: Optional[bool] = False
OPEN_API: Optional[bool] = True
OPEN_API_URL: Optional[str] = "/openapi"
OPEN_API_DESCRIPTION: Optional[str] = "Simple API"

#global CORS policy - optional with defaults
CORS_ENABLED: Optional[bool] = True #use cors
CORS_ALLOW_ORIGINS: Optional[list[str]] = ["*"] #List of allowed origins
CORS_ALLOW_METHODS: Optional[list[str]] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"] #allowed methods
CORS_ALLOW_HEADERS: Optional[list[str]] = ["Authorization", "Content-Type"] #List of allowed headers
CORS_EXPOSE_HEADERS: Optional[list[str]] = [] # List of headers to expose
CORS_ALLOW_CREDENTIALS: Optional[bool] = True #Allow credentials
CORS_MAX_AGE: Optional[int] = None #Max age in seconds. None to disable

# controllers, extensions, models
CONTROLLERS: Optional[List[str]] #import strings
CLI_CONTROLLERS: Optional[List[str]] #import strings
EXTENSIONS: Optional[List[str]] #import strings
MODELS: Optional[List[str]] #import strings
EXCEPTION_HANDLERS: Optional[List[str]] #import strings
```

You can then run the app with a run script:

```
#run.py <-- in the root folder

if __name__ == "__main__":
    import uvicorn
    from app.configs import Config
    configs = Config() #to load default values of user does not provide them
    uvicorn.run("app:Application", host=configs.HOST, port=configs.PORT, lifespan=configs.LIFESPAN, reload=configs.DEBUG, factory=True)
```

```sh
uv run --env-file .env.dev run.py
```

or directly from the terminal with:

```sh
uv run --env-file .env.dev uvicorn app:Application --reload --port 8080 --factory --host localhost
```

This will start the application on localhost on port 8080 with reload enabled (debug mode). The **lifespan** argument is important when you wish to use a database connection or other on_startup/on_shutdown methods. If lifespan="on", uvicorn will give startup/shutdown signals which the app can use to run certain methods. Other lifespan options are: "auto" and "off".

The ***--env-file .env.dev*** can be omitted if environmental variables are not used.

### Startup and shutdown methods

Sometimes we wish to add startup and shutdown methods to our application. One of the most common reasons is connecting to a database at startup and disconnecting at shutdown. In fact, this is what the SqlDatabase extension does automatically (see Extensions section below).
To add such methods, we can add them to the application class implementation like this:

```
from app.configs import Config
from pyjolt import PyJolt, app, on_shutdown, on_startup


@app(__name__, configs = Config)
class Application(PyJolt):

    @on_startup
    async def first_startup_method(self):
        print("Starting up...")

    @on_shutdown
    async def first_shutdown_method(self):
        print("Shuting down...")
```

All methods decorated with the @on_startup or @on_shutdown decorators will be executed when the application starts. In theory, any number of methods can be defined and decorated, however, they will be executed in alphabetical order which can cause issues if not careful. Therefore we suggest you use a single method per-decorator and use it to delegate work to other methods in the correct order. 


## Adding controllers for request handling

Controllers are created as classes with **async** methods that handle specific requests. An example controller is:

```
#app/api/users/user_api.py

from pyjolt import Request, Response, HttpStatus, MediaType
from pyjolt.controller import Controller, path, get, produces, post, consumes
from pydantic import BaseModel

class UserData(BaseModel):
    email: str
    fullname: str

@path("/api/v1/users")
class UsersApi(Controller):

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    async def get_user(self, req: Request, user_id: int) -> Response:
        """Returns a user by user_id"""
        #some logic to load the user

        return req.response.json({
            "id": user_id,
            "fullname": "John Doe",
            "email": "johndoe@email.com"
        }).status(HttpStatus.OK)
    
    @post("/")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def create_user(self, req: Request, user_data: UserData) -> Response[UserData]:
        """Creates new user"""
        #logic for creating and storing user
        return req.response.json(user_data).status(HttpStatus.CREATED)

```
Each endpoint method has access to the application object and its configurations and methods via the self argument (self.app: PyJolt).
The controller must be registered with the application in the configurations:

```
CONTROLLERS: List[str] = [
    'app.api.users.user_api:UserApi' #path:Controller
]
```

In the above example controller the **post** route accepts incomming json data (@consumes) and automatically
injects it into the **user_data** variable with a Pydantic BaseModel type object. The incomming data is also automatically validated
and raises a validation error (422 - Unprocessible entity) if data is incorrect/missing. For more details about data validation and options we suggest you take a look at the Pydantic library. The @produces decorator automatically sets the correct content-type on the 
response object and the return type hint (-> Response[UserData]:) indicates as what type of object the response body should be serialized.

### Available decorators for controllers

```
@path(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
```

This is the main decorator for a controller. It assignes the controller a url path and controlls if the controller should be included in the OpenApi specifications.
It also assignes tag(s) for grouping of controller endpoints in the OpenApi specs.

```
@get(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
@post(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
@put(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
@patch(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
@delete(url_path: str, open_api_spec: bool = True, tags: list[str]|None = None)
```

Main decorator assigned to controller endpoint methods. Determines the type of http request an endpoint handles (GET, POST, PUT, PATCH or DELETE), the endpoint url path (conbines with the controller path), if it should be added to the OpenApi specifications and fine grain endpoint grouping in the OpenApi specs via the **tags** argument.

```
@consumes(media_type: MediaType)
```

Indicates the kind of http request body this endpoint consumes (example: MediaType.APPLICATION_JSON, indicates it needs a json request body.). Available options are:

```
APPLICATION_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"
MULTIPART_FORM_DATA = "multipart/form-data"
APPLICATION_JSON = "application/json"
APPLICATION_PROBLEM_JSON = "application/problem+json"
APPLICATION_XML = "application/xml"
TEXT_XML = "text/xml"
TEXT_PLAIN = "text/plain"
TEXT_HTML = "text/html"
APPLICATION_OCTET_STREAM = "application/octet-stream"
IMAGE_PNG = "image/png"
IMAGE_JPEG = "image/jpeg"
IMAGE_GIF = "image/gif"
APPLICATION_PDF = "application/pdf"
APPLICATION_X_NDJSON = "application/x-ndjson"
APPLICATION_CSV = "application/csv"
TEXT_CSV = "text/csv"
APPLICATION_YAML = "application/yaml"
TEXT_YAML = "text/yaml"
APPLICATION_GRAPHQL = "application/graphql"
NO_CONTENT = "empty"
```

If this decorator is used it must be used in conjuction with a Pydantic data class provided as a parameter in the endpoint method:

```
@post("/")
@consumes(MediaType.APPLICATION_JSON)
@produces(MediaType.APPLICATION_JSON)
async def create_user(self, req: Request, data: TestModel) -> Response[ResponseModel]:
    """Consumes and produces json"""
```

TestModel is a Pydantic class.

```
@produces(media_type: MediaType)
```

The produces decorator indicates and sets the media type of the response body. Although the media type is set automatically it still shows a warning if the actual media type which was set in the endpoint by the developer does not match the intended value.

```
@open_api_docs(*args: Descriptor)
```

This decorator sets the possible return types of the decorated endpoint if the request was not successful (example: 404, 400, 401, 403 response codes). It accepts any number of Descriptor objects:

```
Descriptor(status: HttpStatus = HttpStatus.BAD_REQUEST, description: str|None = None, media_type: MediaType = MediaType.APPLICATION_JSON, body: Type[BaseModel]|None = None)
```

like this:

```
@get("/<int:user_id>")
@produces(MediaType.APPLICATION_JSON)
@open_api_docs(Descriptor(status=HttpStatus.NOT_FOUND, description="User not found", body=ErrorResponse),
                Descriptor(status=HttpStatus.BAD_REQUEST, description="Bad request", body=ErrorResponse))
async def get_user(self, req: Request, user_id: int) -> Response[ResponseModel]:
    """Endpoint logic """
```

The above example adds two possible endpoint responses (NOT_FOUND and BAD_REQUEST) with descriptions and what type of object is returned as json (default).

### Request and Response objects

Each request gets its own Request object which is passed to the controller endpoint method. The Request object contains all
request parameters:

```
req: Request
req.route_parameters -> dict[str, int|str] #route parameters as a dictionary
req.method -> str #http method (uppercase string: GET, POST, PUT, PATCH, DELETE)
req.path -> str #request path (url: str)
req.query_string -> str (the entire query string - what comes after "?" in the url)
req.headers -> dict[str, str] #all request headers
req.query_params -> dict[str, str] #query parameters as a dictionary
req.user -> loaded user (if present). See the authentication implementation below.
req.res -> Response #the Response object
```

The response object provided on the Request object has methods:

```
req.res: Response
req.res.status(self, status_code: int|HttpStatus) -> Self #sets http status code
req.res.redirect(self, location: str, status_code: int|HttpStatus = HttpStatus.SEE_OTHER) -> instructs client to redirect to location
req.res.json(self, data: Any) -> Self #sets a json object as the response body
req.res.no_content(self) -> Self #no content response
req.res.text(self, text: str) -> Self #sets text as the response body
req.res.html_from_string(self, text: str, context: Optional[dict[str, Any]] = None) -> Self #creates a rendered template from the provided string
req.res.html(self, template_path: str, context: Optional[dict[str, Any]] = None) -> Self #creates a rendered template from the template file
req.res.send_file(self, body, headers) -> Self #sends a file as the response
req.res.set_header(self, key: str, value: str) -> Self #sets response header
req.res.set_cookie(self, cookie_name: str, value: str,
                   max_age: int|None = None, path: str = "/",
                   domain: str|None = None, secure: bool = False,
                   http_only: bool = True) -> Self #sets a cookie in the response
delete_cookie(self, cookie_name: str,
                      path: str = "/", domain: Optional[str] = None) -> Self #deletes a cookie
```


### Before and after request handling in Controllers

Sometimes we need to process a request before it ever hits the endpoint. For this, middleware or additional decorators is often used. If only a specific endpoint needs
this pre- or postprocessing, decorators are the way to go, however, if all controller endpoints need it we can add methods to the controller which will run for each request.
We can to this by adding and decorating controller methods:

```
#at the top of the controller file:
from pyjolt.controller import (Controller, path, get, produces, before_request, after_request)
####
@path("/api/v1/users", tags=["Users"])
class UsersApi(Controller):

    @before_request
    async def before_request_method(self, req: Request):
        """Some before request logic"""
    
    @after_request
    async def after_request_method(self, res: Response):
        """Some after request logic"""

    @get("/")
    @produces(MediaType.APPLICATION_JSON)
    async def get_users(self, req: Request) -> Response[ResponseModel]:
        """Endpoint for returning all app users"""
        #await asyncio.sleep(10)
        session = db.create_session()
        users = await User.query(session).all()
        response: ResponseModel = ResponseModel(message="All users fetched.",
                                                status="success", data=None)
        await session.close() #must close the session
        return req.response.json(response).status(HttpStatus.OK)
```

The before and after request methods don't have to return anything. The request/response objects can be manipulated in-place. In theory, any number of methods
can be decorated with the before- and after_request decorators and all will run before the request is passed to the endpoint method, however, they are executed in
alphabetical order which can be combersome. This is why we suggest you use a single method which calls/delegates work to other methods.

## CORS

PyJolt has built-in CORS support. There are several configurations which you can set to in the Config class to configure CORS.
Configuration options with default values are:

```
CORS_ENABLED: Optional[bool] = True #use cors
CORS_ALLOW_ORIGINS: Optional[list[str]] = ["*"] #List of allowed origins
CORS_ALLOW_METHODS: Optional[list[str]] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"] #allowed methods
CORS_ALLOW_HEADERS: Optional[list[str]] = ["Authorization", "Content-Type"] #List of allowed headers
CORS_EXPOSE_HEADERS: Optional[list[str]] = [] # List of headers to expose
CORS_ALLOW_CREDENTIALS: Optional[bool] = True #Allow credentials
CORS_MAX_AGE: Optional[int] = None #Max age in seconds. None to disable
```

The above configurations will set CORS policy on the application scope. If you wish to fine-tune the policy on specific 
endpoints you can use two decoratos.

To disable cors on an endpoint:

```
#imports
from pyjolt.controller import no_cors

#inside a controller

@GET("/")
@no_cors
async def my_endpoint(self, req: Request) -> Response:
    """some endpoint logic"""
```

this will disable CORS for this specific endpoint no matter the global settings.

If you wish you can set a different set of CORS rules for an endpoint using the ***@cors*** decorator:

```
#imports
from pyjolt.controller import cors

#inside a controller

@GET("/")
@cors(*,
    allow_origins: Optional[list[str]] = None,
    allow_methods: Optional[list[str]] = None,
    allow_headers: Optional[list[str]] = None,
    expose_headers: Optional[list[str]] = None,
    allow_credentials: Optional[bool] = None,
    max_age: Optional[int] = None,)
async def my_endpoint(self, req: Request) -> Response:
    """some endpoint logic"""
```

This will override the global CORS settings with endpoint-specific settings.

### CORS responses

If the request does not comply with CORS policy error responses are automatically returned:

**403 - Forbiden** - if the request origin is not allowed
**405 - Method not allowed** - if the request method is not allowed

## Routing

PyJolt uses the same router as Flask under the hood (Werkzeug). This means that all the same patterns apply.

Examples:
```
@get("/api/v1/users/<int:user_id>)
@get("/api/v1/users/<string:user_name>)
@get("/api/v1/users/<path:path>) #handles: "/api/v1/users/account/dashboard/main"
```

Route parameters marked with "<int:>" will be injected into the handler as integers, "<string:>" as a string and "<path:>" injects the entire path as a string.

### Route not found

If a route is not found (wrong url or http method) a NotFound (from pyjolt.exception import NotFound) error is raised. You can handle the exception in the ExceptionHandler class. If not handled, a generic JSON response is returned.

## Exception handling

Exception handling can be achived by creating an exception handler class (or more then one) and registering it with the application.

```
# app/api/exceptions/exception_handler.py

from typing import Any
from pydantic import BaseModel, ValidationError
from pyjolt.exceptions import ExceptionHandler, handles
from pyjolt import Request, Response, HttpStatus

from .custom_exceptions import EntityNotFound

class ErrorResponse(BaseModel):
    message: str
    details: Any|None = None

class CustomExceptionHandler(ExceptionHandler):
    
    @handles(ValidationError)
    async def validation_error(self, req: "Request", exc: ValidationError) -> "Response[ErrorResponse]":
        """Handles validation errors"""
        details = {}
        if hasattr(exc, "errors"):
            for error in exc.errors():
                details[error["loc"][0]] = error["msg"]

        return req.response.json({
            "message": "Validation failed.",
            "details": details
        }).status(HttpStatus.UNPROCESSABLE_ENTITY)
```

The above CustomExceptionHandler class can also be registered with the application in configs.py file.

```
EXCEPTION_HANDLERS: List[str] = [
    'app.api.exceptions.exception_handler:CustomExceptionHandler'
]
```

You can define any number of methods and decorate them with the @handles decorator to indicate which exception
should be handled by the method. The @handles decorator excepts any number of exceptions as arguments.

Any exceptions that are raised throughout the app can be handled in one or more ExceptionHandler classes. If an unhandled exception occurs
and the application is in DEBUG mode, the exception will raise an error, however, if the application is NOT in DEBUG mode, the exception is
suppressed and a JSON response with content 

```
{
    "status": "error",
    "message": "Internal server error",
}
```

with status code 500 (Internal server error) is returned and the request is logged as critical. 
To avoid this generic response you can implement a handler in your ExceptionHandler class which handles raw exceptions (pythons Exception class).

```
@handles(ValidationError, SomeOtherException, AThirdException)
async def handler_method(self, req: "Request", exc: ValidationError|SomeOtherException|AThirdException) -> "Response[ErrorResponse]":
    ###handler logic and response return
```

Each handler method accepts exactly three arguments. The "self" keyword pointing at the exception handler instance (has acces to the application object -> self.app),
the current request object and the raised exception.

### Custom exceptions

Custom exceptions can be made by defining a class which inherits from the pyjolt.exceptions.BaseHttpException, from the pyjolt.Exceptions.CustomException or simply by inheriting from pythons Exception class.

```
from pyjolt.exception import BaseHttpException, CustomException

class MyCustomException(Exception):
    """implementation"""

class MyCustomHttpException(BaseHttpException):
    """implementation"""

class CustomExceptionFromCustomException(CustomException):
    """implementation"""
```

The exceptions can then be registered with your exception handler to provide required responses to users.

### Quick aborts

Sometimes, you just wish to quickly abort a request (when data is not found, something else goes wrong.). Since PyJolt advocates for the
fail-fast pattern, it provides two convinience methods for quickly aborting requests. These methods are:

```
from pyjolt import abort, html_abort
abort(msg: str, status_code: HttpStatus = HttpStatus.BAD_REQUEST, status: str = "error", data: Any = None)
html_abort(template: str, status_code: HttpStatus = HttpStatus.BAD_REQUEST, data: Any = None)
```

These methods raise a AborterException and HtmlAborterException, respectively. An example of the abort method use;

```
from pyjolt import abort, html_abort

@get("/api/v1/users/<int:user_id>)
async def get_user(self, req: Request, user_id: int) -> Response:
    """Handler logic"""
    #Entity not found
    abort(msg=f"User with id {user_id} not found",
        status_code=HttpStatus.NOT_FOUND,
        status="error", data=None)
```

To handle AborterExceptions you have to implement a handler in your ExceptionHandler class, however, HtmlAborterExceptions are automatically
rendered and returned.

### Redirecting
Sometimes we wish to redirect the user to a different resource. In this case we can use a redirect response of the Response object.

```
@get("/api/v1/auth/login)
async def get_user(self, req: Request, data: UserLoginData) -> Response:
    """Handler logic"""
    #Redirect after login
    return req.response.redirect("url-for-location")
```

The above example instructs the client to redirect to "url-for-location" with default status code 303 (SEE OTHER).

### Redirecting to other endpoint

We can provide a hard-coded string to the ***redirect*** method, however, this can be cumbersome. The url might change and the redirect would break.
To avoid this, we can use the url_for method provided by the application object: 

```
#Redirect after login
return req.response.redirect(self.app.url_for("<ControllerName>.<endpointMethodName>"), **kwargs)
```

This will construct the correct url with any route parameters (provided as key-value pairs <-> kwargs) and return it as a string.
In this way, we do not have to hard-code and remember all urls in our app. We can also change the non-dynamic parts of the endpoint
without breaking redirects.


## Static assets/files

The application serves files in the "/static" folder on the path "/static/<path:filename>".
If you have an image named "my_image.png" in the static folder you can access it on the url: http://localhost:8080/static/my_image.png
The path ("/static") and folder name ("/static") can be configured via the application configurations. The folder should be inside the "app" folder.

To construct the above example url for ***my_image.png*** we can use the ***url_for*** method like this:

```
self.app.url_for("Static.get", filename="my_image.png")
```

This will return the correct url for the image. If the image was located in subfolders we would simply have to change the ***filename** argument
in the method call.

In this example, the url_for method returns the url for the ***get*** method of the ***Static*** controller (automatically registered by the application)
with required ***filename*** argument.

## Template (HTML) responses

Controller endpoints can also return rendered HTML or plain text content.

```
#inside a controller class

@get("/<int:user_id>")
@produces(MediaType.TEXT_HTML)
async def get_user(self, req: Request, user_id: int) -> Response:
    """Returns a user by user_id"""
    #some logic to load the user
    context: dict[str, Any] = {#any key-value pairs you wish to include in the template}

    return await (req.response.html("my_template.html", context)).status(HttpStatus.OK)
```

The template name/path must be relative to the templates folder of the application. Because the html response accesses/loads the template 
from the templates folder, the .html method of the response object is async and must thus be awaited.

The name/location of the templates folder can be configured via application configurations.

PyJolt uses Jinja2 as the templating engine, the synatx is thus the same as in any framework which uses the same engine.

## OpenAPI specifications

OpenAPI specifications are automatically generated and exposed on "/openapi/docs" (Swagger UI) and "/openapi/specs.json" endpoints (in Debug mode only).
To make sure the endpoint descriptions, return types and request specification are accurate, we suggest you use all required endpoint decorators available for
endpoints.

## Extensions
PyJolt has a few built-in extensions that can be used ad configured for database connection/management, task scheduling, authentication and 
interfacing with LLMs.

### Database connectivity and management

To add database connectivity to your PyJolt app you can use the database module.

```
#extensions.py
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate

db: SqlDatabase = SqlDatabase(db_name="db") #db is the default so it can be omitted
migrate: Migrate = Migrate(db, command_prefix: str = "")
```

you can then indicate the extensions in the app configurations:

```
EXTENSIONS: List[str] = [
    'app.extensions:db',
    'app.extensions:migrate'
]
```

This will initilize and configure the extensions with the application at startup. To configure the extensions simply add
neccessary configurations to the config class or dictionary. Available configurations are:

**SqlDatabase**
```
DATABASE_URI: str = sqlite+aiosqlite:///./test.db #for a simple SQLite db
```
To use a Postgresql db the **DATABASE_URI** string should be like this:
```
DATABASE_URI: str = postgresql+asyncpg://user:pass@localhost/dbname
```

Session name variable (for use with @managed_session):
```
DATABASE_SESSION_NAME: str = "session"
```
This is the name of the AsyncSession variable that is injected when using the managed_session decorator of the extension. The default is "session". This is useful when you wish to use
managed sessions for multiple databases in the same controller endpoint.

**Migrate**
```
ALEMBIC_MIGRATION_DIR: str = "migrations" #default folder name for migrations
ALEMBIC_DATABASE_URI_SYNC: str = "sqlite:///./test.db" #a connection string with a sync driver
```

The SqlDatabase extension accepts a variable_prefix: str argument which is passed to its Migrate instance. The Migrate instance can be passed a
command_prefix: str which can be used to differentiate different migration instances if uses multiple (for multiple databases).
```
#extensions.py
.
.
.
db: SqlDatabase = SqlDatabase(variable_prefix="MY_DB_")
migrate: Migrate = Migrate(db: SqlDatabase, command_prefix: str = "")
```

In this case the configuration variables should be:
```
MY_DB_DATABASE_URI: str
MY_DB_ALEMBIC_MIGRATION_DIR: str
MY_DB_ALEMBIC_DATABASE_URI_SYNC: str
```
This is useful in cases where you need more then one database.

The migrate extension exposes some function which facilitate database management.
They can be envoked via the cli.py script in the project root

```
#cli.py <- next to the run.py script
"""CLI utility script"""

if __name__ == "__main__":
    from app import Application
    app = Application()
    app.run_cli()
```

You can run the script with command like this:
```sh
uv run cli.py db-init
uv run cli.py db-migrate --message "Your migration message"
uv run cli.py db-upgrade
```
The above commands initialize the migrations tracking of the DB, prepares the migration script and finally upgrades the DB.

Other available cli commands for DB management are:

```
db-downgrade --revision "rev. number"
db-history --verbose --indicate-current
db-current --verbose
db-heads --verbose
db-show --revision "rev. number"
db-stamp --revision "rev. number"
```

Arguments to the above commands are optional.

**If using command_prefix**
If using a command prefix for the Migrate instance the commands can be executed like this:

```
uv run cli.py <command_prefix>db-init
uv run cli.py <command_prefix>db-migrate --message "Your migration message"
uv run cli.py <command_prefix>db-upgrade
```

The same applies to other commands of the Migrate extension.

**The use of the Migrate extension is completely optional when using a database.**

### Database Models
To store/fetch data from the database you can use model classes. An example class is:

```
#app/api/models/user_model.py

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from pyjolt.database import create_declerative_base

Base = create_declerative_base("db") #passed argument must be the same as the database name you wish to
                                    #use the model with. Default is "db" so it can be omitted.

class User(Base):
    """
    User model
    """
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(50), unique=True)
```

The Base class created with create_declerative_base should be used with all db models for the same database. 

#### Querying
To perform queries in the database you can use the associated models. A simple query for getting a user by its ID is:

```
user: User = await User.query(session).filter_by(id=user_id).first()
```

This returns the first user that matches the filter_by criteria. To get all users in the table you can do:

```
users:  list[User] = await User.query(session).all()
```

**Don't forget to close the session if you are not using automatic session handling**

The ***Model.query(session)*** method returns an AsyncQuery object which exposes many methods for querying and filtering:

```
def where(self, *conditions) -> "AsyncQuery": #Adds WHERE conditions (same as `filter()`).
def filter(self, *conditions) -> "AsyncQuery": #Adds WHERE conditions to the query (supports multiple conditions).
def filter_by(self, **kwargs) -> "AsyncQuery": #Adds WHERE conditions using keyword arguments (simpler syntax).
def join(self, other_model: Model) -> "AsyncQuery": #Performs a SQL JOIN with another model.
def limit(self, num: int) -> "AsyncQuery": #"Limits the number of results returned.
def offset(self, num: int) -> "AsyncQuery": #Skips a certain number of results (used for pagination).
def order_by(self, *columns) -> "AsyncQuery": Sorts results based on one or more columns.
def like(self, column, pattern, escape=None) -> "AsyncQuery": #Filters results using a SQL LIKE condition.
def ilike(self, column, pattern, escape=None) -> "AsyncQuery": #Filters results using a SQL ILIKE condition.
```

The above methods always return the AsyncQuery object and thus serve as query builders. This means that the methods can be chained to construct the desired query. 
Actual results are returned once we execute the query with one of the following methods (must be awaited):

```
async def count(self) -> int: #returns number of results
async def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]: #returnes a dictionary with paginated results (see below)
async def all(self) -> list: #returns all results
async def first(self) -> Any: #returns first result
async def one(self) -> Any: #returns only one result
```

##### Paginated results

The paginate method returns a pagination object (dictionary) with the following structure:

```
result = dict: {
    "items": list[Model], #List of results
    "total": int, #Total records
    "page": int, #Current page
    "pages": int, #Total pages
    "per_page": int, #Results per page
    "has_next": bool, #Whether there's a next page
    "has_prev": bool #Whether there's a previous page
}
```

**For model detection (for correct Migration extension working) all models should be added in the app configurations**

```
MODELS: List[str] = [
    'app.api.models.user_model:User'
]
```

**SqlDatabase and Migrate extension uses Sqlalchemy and Alembic under the hood.**

### Automatic session handling

Because it is easy to forget to close/commit an active session a convenience decorator can be used:

```
@post("/")
@consumes(MediaType.APPLICATION_JSON)
@produces(MediaType.APPLICATION_JSON)
@db.managed_session
async def get_user(self, req: Request, user_data: UserData, session: AsyncSession) -> Response[UserData]:
    """Creates new user"""
    user: User = User(fullname=user_data.fullname, email=user_data.email)
    session.add(user)
    await session.flush() #to get the new users id.
    return req.response.json(UserData(id=user_id, fullname=user.fullname)).status(HttpStatus.OK)
```

This automatically injects the active session **(with the name "session" !!!!)** into the endpoint handler and runs the endpoint inside a session context, which handles
session closure/commit (manual commit is no longer neccessary) and possible rollbacks in case of errors. In the case of an error, a rollback is performed and then the exception is re-raised. 
This means that any errors must be handled for a successful response.

**session.flush()** will cause the session to perform the insert and fetch the objects id(s).

## User Authentication

To setup user authentication and protection of controller endpoints use the authentication extension.

```
#authentication.py <- next to extensions.py

from enum import StrEnum
from typing import Optional
from pyjolt import Request
from pyjolt.auth import Authentication

from app.extensions import db
from app.api.models import User

class UserRoles(StrEnum):
    ADMIN = "admin"
    SUPERUSER = "superuser"
    USER = "user"

class Auth(Authentication):

    async def user_loader(self, req: Request) -> Optional[User]:
        """Loads user from the provided cookie"""
        cookie_header = req.headers.get("cookie", "")
        if cookie_header:
            # Split the cookie string on semicolons and equals signs to extract individual cookies
            cookies = dict(cookie.strip().split('=', 1) for cookie in cookie_header.split(';'))
            auth_cookie = cookies.get("auth_cookie")
            if auth_cookie:
                user_id = self.decode_signed_cookie(auth_cookie)
                if user_id:
                    session = db.create_session()
                    user = await User.query(session).filter_by(id=user_id).first()
                    await session.close()
                    return user
        return None

    async def role_check(self, user: User, roles: list[UserRoles]) -> bool:
        """Checks intersection of user roles and required roles"""
        user_roles = set([role.role for role in user.roles])
        return len(user_roles.intersection(set(roles))) > 0

auth: Auth = Auth()
```

The Auth class inherits from the PyJolt Authentication class. The user must implement the user_loader and role_check (optional) methods.
These methods provide logic for loading a user when a protected endpoint is requested and checking if the user has permissions.
Above is an example which loads the user from a cookie. If the user is not found an AuthenticationException is raised which can be handled
in the CustomExceptionHandler. If the user doesn't have required roles (role_check -> False) an UnauthorizedException exception is raised
which can be also handled in the CustomExceptionHandler.

The instantiated Auth class must be added to the application configs.

```
EXTENSIONS: List[str] = [
    'app.extensions:db',
    'app.extensions:migrate',
    'app.authentication:auth'
]
```

Controller endpoints can be protected with two decorators like this:

```
@get("/<int:user_id>")
@produces(MediaType.APPLICATION_JSON)
@auth.login_required
@auth.role_required(UserRoles.ADMIN, UserRoles.SUPERUSER)
async def get_user(self, req: Request, user_id: int) -> Response[UserData]:
    """Returns a user by user_id"""
    session = db.create_session()
    user: User = await User.query(session).filter_by(id=user_id).first()
    await session.close()

    return req.response.json(UserData(id=user_id, fullname=user.fullname, email=user.email)).status(HttpStatus.OK)
```

If using the @auth.role_required decorator you MUST also use the @auth.login_required decorator. The login_required
decorator calls the user_loader method and attaches the loaded user object to the Request object: **req.user**.
The above role_check implementation assumes that there is a one-to-many relationship on the User and Role (not shown) models.

The Authentication extension can be configured with the following options:

```
AUTHENTICATION_ERROR_MESSAGE: str = "Login required" #message of the raised exception
UNAUTHORIZED_ERROR_MESSAGE: str = "Missing user role(s)" #message of the raised exception
```

The auth instance exposes other useful methods for easy user authentication:

```
auth.create_signed_cookie_value(self, value: str|int) -> str #creates a signed cookie
auth.decode_signed_cookie(self, cookie_value: str) -> str #decodes signed cookie
auth.create_password_hash(self, password: str) -> str #creates a password hash
auth.check_password_hash(self, password: str, hashed_password: str) -> bool #check password hash against provided password
auth.create_jwt_token(self, payload: Dict, expires_in: int = 3600) -> str #creates a JWT string
auth.validate_jwt_token(self, token: str) -> Dict|None #validates JWT string (from request)
```

The decode_signed_cookie method is used in the above user_loader example.

## Task scheduling

The task_manager extensions allows for easy management of tasks that should run periodically or running of one-time fire&forget methods.
To use the extension you have to install the neccessary dependencies with:

```
uv add "pyjolt[scheduler]"
```

The extension can be setup like this:

```
#scheduler.py <- next to __init__.py

from pyjolt.task_manager import TaskManager, schedule_job

class Scheduler(TaskManager):

    @schedule_job("interval", minutes=1, id="my_job")
    async def some_task(self):
        print("Performing task")

scheduler: Scheduler = Scheduler()
```

It can then be added to application configs like the Authentication extension.

```
EXTENSIONS: List[str] = [
    'app.extensions:db',
    'app.extensions:migrate',
    'app.authentication:auth',
    'app.scheduler:scheduler'
]
```

All methods defined in the Scheduler class and decorated with the @schedule_job decorator will be run with provided parameters. The extension uses the APScheduler
module we therefore recommend you take a look at their documentation for more details about job scheduling. In the above example, the "some_task" method will run
as an interval method every minute. To use the extension to run fire&forget methods (like sending emails) where we don't neccessary have to wait for the method to finish
we can use the run_background_task method:

```
from app.scheduler import scheduler


@post("/")
@consumes(MediaType.APPLICATION_JSON)
@produces(MediaType.APPLICATION_JSON)
async def get_user(self, req: Request, user_data: UserData) -> Response[UserData]:
    """Creates new user"""
    user: User = User(fullname=user_data.fullname, email=user_data.email)
    session = db.create_session()
    session.add(user)
    await session.commit()

    scheduler.run_background_task(send_email, *args, **kwargs) #args and kwargs are any number or arguments and keyword arguments that the send_mail method might need
    return req.response.json(UserData(id=user_id, fullname=user.fullname)).status(HttpStatus.OK)
```

This kicks off the send_email method without waiting for it to finish.

The extension accepts the following configuration options via the application (indicated are defaults):

```
TASK_MANAGER_JOB_STORES = {
        'default': MemoryJobStore()
    }
TASK_MANAGER_EXECUTORS = {
        'default': AsyncIOExecutor()
    }
TASK_MANAGER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }
TASK_MANAGER_DAEMON: bool = True
TASK_MANAGER_SCHEDULER = AsyncIOScheduler
```

The scheduler object exposes a number of methods which can be used to manupulate ongoing scheduled tasks:

```
scheduler.add_job(self, func: Callable, *args, **kwargs) -> Job #adds a Job to the scheduler
scheduler.remove_job(self, job: str|Job, job_store: Optional[str] = None) #removes job from scheduler by its id:str or the Job object
scheduler.pause_job(self, job: str|Job) #pauses a running job by job id:str or the Job object
scheduler.resume_job(self, job: str|Job) #resumes a job by job id:str or the Job object
scheduler.get_job(self, job_id: str) -> Job|None #returns the job if it exists
```

## Caching

Caching is a simple method to increase the throughput of applications. It stores responses of frequently requested resources whos data
doesn't change often. An example would be fetching all users of an app, where new users are not added often. Why do database queries for each
request if the query result is always going to be the same. To prevent unneccessary database queries the controller endpoint response can be cached
with the caching extensions. To use it, you have to first install the dependecies:

```
uv add "pyjolt[cache]"
```

After this, you can add the extension to your app with:

```
#extensions.py <-next to __init__.py

from pyjolt.caching import Cache

#other extensions
cache: Cache = Cache()
```

and then you can add the instantiated extension application configs:

```
EXTENSIONS: List[str] = [
    'app.extensions:db',
    'app.extensions:migrate',
    'app.authentication:auth',
    'app.scheduler:scheduler',
    'app.extensions:cache'
]
```

The cache can use in-memory caching (default) or a Redis database. To use the in-memory cache no configurations are strictly neccessary.
Available configurations:

```
CACHE_REDIS_URL: str
CACHE_DURATION: int = 300 #cache duration in seconds
CACHE_REDIS_PASSWORD: str
```

Only the default cache duration can be set if using in-memory caching. The default value is 300 seconds.

Once configured the caching extension can be used like this in controller endpoints:

```
@get("/<int:user_id>")
@produces(MediaType.APPLICATION_JSON)
@cache.cache(duration=300)#default is 300 so this is not needed
async def get_user(self, req: Request, user_id: int) -> Response[UserData]:
    """Returns a user by user_id"""
    user: User = await User.query().filter_by(id=user_id).first()

    return req.response.json(UserData(id=user_id, fullname=user.fullname, email=user.email)).status(HttpStatus.OK)
```

The @cache.cache decorator MUST be applied as the bottom-most decorator to make sure it caches the result of the actual
endpoint function and NOT results of other decorators. This is especially crucial if using authentication.

The caching extension stores the result of the endpoint by creating a key-value pair, where the key is a combination
of the endpoint function name and route parameters. This makes sure that the endpoint stores the response for user_id=1 and user_id=2
seperately. 

The extension exposes several methods on the cache object which allows for manual manipulation of the cache:

```
cache.set(key: str, value: Response, duration: Optional[int]) -> None #sets a cached key-value pair
cache.get(key: str) -> Dict #gets the cache value for the provided key
cache.delete(key: str) -> None #removes cache entry for the provided key
cache.clear() -> None #clears entire cache
```

## AI Interface (Experimental!)

The AI Interface extension helps the user integrate a chat interface to popular vendors with ChatGPT compatible api's seemlesly. You must first install the needed dependencies with:

```
uv add "pyjolt[ai_interface]"
```

This will install OpenAi, Torch, Numpy, Sentence-transformers and pgvector libraries. These are neccessary for all required funcionality. With this, you will be able to connect to any ChatGPT compatible api like Groq, xAI, Perplexity (Sonar), Google Gemini and locally hosten Ollama, LM Studio or VLLM.

The extension accepts several configurations which are listed below (with defaults):

```
AI_INTERFACE_API_KEY: str #required
AI_INTERFACE_API_BASE_URL: Optional[str] = "https://api.openai.com/v1" #points to the OpenAi compatible api of the service
AI_INTERFACE_ORGANIZATION_ID: Optional[str] = None
AI_INTERFACE_PROJECT_ID: Optional[str] = None
AI_INTERFACE_TIMEOUT: Optional[int] = 30
AI_INTERFACE_MODEL: Optional[str] = "gpt-3.5-turbo" #model that is used
AI_INTERFACE_TEMPERATURE: Optional[float] = 1.0 #temperature (randomness) of the used model. For higher "creativity"
AI_INTERFACE_RESPONSE_FORMAT: Optional[dict[str, str]] = {"type": "json_object"} #format of the return object
AI_INTERFACE_TOOL_CHOICE: Optional[bool] = False #if AI tools can be used
AI_INTERFACE_MAX_RETRIES: Optional[int] = 0 #number of retries in case of failure
AI_INTERFACE_CHAT_CONTEXT_NAME: Optional[str] = "chat_context" #name of the injected chat context varible
```

To implement the interface:

```
#ai_interface.py #next to __init__.py

from typing import Optional

from app.api.models.chat_session import ChatSession
from app.extensions import db

from pyjolt.database import AsyncSession
from pyjolt.ai_interface import AiInterface
from pyjolt.request import Request


class Interface(AiInterface):

    @db.managed_session
    async def chat_context_loader(self, req: Request,
                                  session: AsyncSession) -> Optional[ChatSession]:
        chat_session_id: Optional[int] = req.route_parameters.get("chat_session_id",
                                                                  None)
        if chat_session_id is None:
            return None
        return await ChatSession.query(session).filter_by(id = chat_session_id).first()

ai_interface: Interface = Interface()
```

Then simply include the ai_interface in the application configs like before to load and register it with the app:

```
#configs.py

EXTENSIONS: list[str] = [
    'app.extensions:db',
    'app.extensions:migrate',
    'app.authentication:auth',
    'app.ai_interface:ai_interface'
]
```

When implementing the interface you have to provide the ***chat_context_loader*** method which at minimum accepts the ***self*** argument pointing at the extension (has access to the application via ***self.app***) and the current request. The above example
also adds the ***@db.managed_session*** decorator for automatic injection and handling of database sessions. The implemented method must return None (when the chat context was not found) or the chat context object (database model). If the method returns None, the extension raises a ChatContextNotFound exception (from pyjolt.ai_interface import ChatContextNotFound). This error can simply be handled in the ExceptionHandler implementation (see above).

If the method returns a valid object (not None), the object is injected into the endpoint handler method with the configured chat context name (default: "chat_context"). This helps with loading existing chat contexts and keeps the endpoint handlers lean.

### AI Tools

You can also expose certain functions to the AI interface which can be called directly by the AI. This is useful to run methods like getting the current weather in a location. The exposed methods must be declared inside the interface class (next to the chat_context_loader) and decorated with the ***@tool*** decorator. Example:

```
from pyjolt.ai_interface import tool

class Interface(AiInterface):

    #chat_context_loader implementation

    @tool(name = "method_name", description: "method_description")
    async def some_tool(self, arg1: str, arg2: str) -> Any:
        """some tool logic"
```

The above example exposes the method ***some_method*** to the AI interface. The decorator ***@tool*** accepts to optional arguments (name and description). If none are provided the actual method name is used and the doc string for the description. The description helps the AI interface (the called LLM) determine which method should be called. Therefore it is recommended to provide concise and accurate descriptions. The exposed method is not just exposed but also analyzed and a method metadata object is constructed which also provides details about the implemented method (arguments, arguments types etc.). With this added metadata the AI (called LLM) can determine which arguments it must pass to the method or if any arguments are missing.

If execution of the tool method failes for whatever reason, a "FailedToRunAiToolMethod" exception is raised which can be handled in the ExceptionHandler implementation.

The number of method tools is not limited, however, we recommend to seperate them into subclasses which the main interface class can inherit from (in addition to the AiInterface class). In this way, you can keep the tools logically grouped.

## Command line interface

If you wish you can create command line interface utility methods to help with application maintanence. To do so you have to use the CLIController class:

```
#app/cli/cli_controller.py

from pyjolt.cli import CLIController, command, argument

class UtilityCLIController(CLIController):
    """A simple CLI utility controller."""

    @command("greet", help="Greet a user with a message.")
    @argument("name", arg_type=str, description="The name of the user to greet.")
    async def greet(self, name: str):
        """Greet by name."""
        print(f"Hello, {name}! Welcome to the CLI utility.")

    @command("add", help="Add two numbers.")
    @argument("a", arg_type=int, description="The first number.")
    @argument("b", arg_type=int, description="The second number.")
    async def add(self, a: int, b: int):
        """Add two numbers and print the result."""
        result = a + b
        print(f"The sum of {a} and {b} is {result}.")
```

In this controller you can add as many cli method as you wish with the use of the @command and @argument decorators. The ***self*** keyword points at the controller instance which has access to the application instance (***self.app: PyJolt***).
Each command method requires the @command decorator, but the @argument decorator(s) are optional depending on if the method needs input from the user or not.

### @command
The @command decorator requires a coommand_name: str argument under which the command will be accessible. You can also provide a ***help*** argument detailing the purpose of the method and options.

### @argument
You can add as many @argument decorators as you wish to a method. This decorator tells the parser what arguments (name) to except and in what data type these arguments are going to be. PyJolt automatically casts arguments
into the provided type. Allowed types are ***int***, ***float*** and ***str***. 

After you have created the CLI controller you have to register it with the application. To do so you have to add it in the application configurations

```
CLI_CONTROLLERS: List[str] = [
    'app.cli.cli_controller:UtilityCLIController' #path:CLIController
]
```

## Testing

PyJolt uses Pytest for running tests. For creating tests use the PyJoltTestClient object from ***pyjolt.testing***.
We recommend creating a ***tests*** folder inside your ***app*** directory (next to templates and static folders). You may organize tests differently as long as you follow Pytest’s discovery rules.

### Configuring test client

Inside the ***tests*** folder create a **conftest.py** file with the following content:

```
# tests/conftest.py

import pytest
from pyjolt.testing import PyJoltTestClient
from app import Application

@pytest.fixture
async def application():
    yield Application()

@pytest.fixture
async def client(application):
    async with PyJoltTestClient(application) as c:
        yield c
```

this creates and yields the test client for use in all test methods. The test client manages lifespan events using asgi_lifespan, so any startup/shutdown hooks will work just like when running the app with Uvicorn.
Inside the ***tests*** folder you can create as many test files as you wish. To can also organize them into subfolders as long as you follow **Pytest naming conventions**. An example test file is:

```
#tests/test_user_api.py

async def test_get_users(client):
    res = await client.get("/api/v1/users")
    assert res.status_code == 200

```

In this file there is a single method (test_get_users) which gets the PyJoltTestClient automatically injected. It makes a GET request to the "/api/v1/users" endpoint and asserts that the response
status code is 200 (OK). If the assertion fails the test fails.

### Running tests

If you use uv for dependency management you can run all specified tests with the following command:

```
uv run --env-file path/to/.env pytest
```

this will load environmental variables and run pytest. Pytest automatically detects the ***tests** folder and all specified tests (if proper naming conventions are followed). If you don't use .env files
you can ommit "--env-file path/to/.env".

#### Pytest configs

If using ***uv*** for dependency management you can add configurations for Pytest to the pyproject.toml file. Otherwise, look up configuration handling. uv example:

```
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```
