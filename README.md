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

If you wish to start without the template you can do that ofcourse. However, we recommend you have a look at the template structure to see how to organize your project.
It is recommended to use the application factory pattern (a factory function which returns the configured application object).
A minimum example would be:

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
    SECRET_KEY: str = "46373hdnsfshf73462twvdngnghjdgsfd" #change for a secure random string
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

# controllers, extensions, models
CONTROLLERS: Optional[List[str]] #import strings
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
    uvicorn.run("app:Application", host=Config.HOST, port=Config.PORT, lifespan=Config.LIFESPAN, reload=Config.DEBUG, factory=True)
```

```sh
uv run --env-file .env.dev run.py
```

or directly from the terminal with:

```sh
uv run --env-file .env.dev uvicorn app:Application --reload --port 8080 --factory --host localhost
```

This will start the application on localhost on port 8080 with reload enabled (debug mode). The **lifespan** argument is important when you wish to use a database connection or other on_startup/on_shutdown methods. If lifespan="on", uvicorn will give startup/shutdown signals which the app can use to run certain methods. Other lifespan options are: "auto" and "off".

### Global before and after request handling

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
from pyjolt.controller import Controller, path, get, produces
from pydantic import BaseModel

class UserData(BaseModel):
    email: str
    fullname: str

@path("/api/v1/users)
class UserApi(Controller):

    @get("/<int:user_id>")
    @produces(MediaType.APPLICATION_JSON)
    async def get_user(self, req: Request, user_id: int) -> Response:
        """Returns a user by user_id"""
        #some logic to load the user

        return req.response.json({
            "id": user_id,
            "fullname": "John Doe",
            "email": johndoe@email.com
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
        return req.response.json(response).status(HttpStatus.OK)
```

The before and after request methods don't have to return anything. The request/response objects can be manipulated in-place. In theory, any number of methods
can be decorated with the before- and after_request decorators and all will run before the request is passed to the endpoint method, however, they are executed in
alphabetical order which can be combersome. This is why we suggest you use a single method which calls/delegates work to other methods.


## Exception handling

Exception handling can be achived by creating an exception handler class and registering it with the application.

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

The above CustomExceptionHandler class can also be registered with the application in configs.py file

```
EXCEPTION_HANDLERS: List[str] = [
    'app.api.exceptions.exception_handler:CustomExceptionHandler'
]
```

You can define any number of methods and decorate them with the @handles decorator to indicate which exception
should be handled by the method. The @handles decorator excepts any number of exceptions as arguments.

```
@handles(ValidationError, SomeOtherException, AThirdException)
async def handler_method(self, req: "Request", exc: ValidationError|SomeOtherException|AThirdException) -> "Response[ErrorResponse]":
    ###handler logic and response return
```

Each handler method accepts exactly three arguments. The "self" keyword pointing at the exception handler instance (has acces to the application object),
the current request object and the raised exception.

## Static assets/files

The application serves files in the "/static" folder on the path "/static/<path:filename>".
If you have an image named "my_image.png" in the static folder you can access it on the url: http://localhost:8080/static/my_image.png
The path ("/static") and folder name ("/static") can be configured via the application configurations. The folder should be inside the "app" folder.

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

**For model detection (for correct Migration extension working) all models should be added in the app configurations**

```
MODELS: List[str] = [
    'app.api.models.user_model:User'
]
```

**SqlDatabase and Migrate extension uses Sqlalchemy and Alembic under the hood.**

Models like this can be used in controller endpoints for storing/fetching like this:

```
from app.extension import db

@get("/<int:user_id>")
@produces(MediaType.TEXT_HTML)
async def get_user(self, req: Request, user_id: int) -> Response[UserData]:
    """Returns a user by user_id"""
    session = db.create_session()
    user: User = await User.query(session).filter_by(id=user_id).first()

    return req.response.json(UserData(id=user_id, fullname=user.fullname, email=user.email)).status(HttpStatus.OK)

@post("/")
@consumes(MediaType.APPLICATION_JSON)
@produces(MediaType.APPLICATION_JSON)
async def get_user(self, req: Request, user_data: UserData) -> Response[UserData]:
    """Creates new user"""
    session = db.create_session()
    user: User = User(fullname=user_data.fullname, email=user_data.email)
    session.add(user)
    await session.commit()

    return req.response.json(UserData(id=user_id, fullname=user.fullname)).status(HttpStatus.OK)
```

## User Authentication

To setup user authentication and protection of controller endpoints use the authentication extension.

```
#authentication.py <- next to extensions.py

from enum import StrEnum
from typing import Optional
from pyjolt import Request
from pyjolt.auth import Authentication

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
                    user = await User.query().filter_by(id=user_id).first()
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
    user: User = await User.query().filter_by(id=user_id).first()

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


