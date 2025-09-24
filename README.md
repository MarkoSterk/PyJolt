# PyJolt - async first python web framework

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

from pyjolt import PyJolt
from app.configs import Config

def create_app(configs: Config): -> PyJolt

    app: PyJolt = PyJolt(__name__)
    app.configure_app(configs)

    return app

```

and the configuration object is:
```
#app/configs.py <-- in the app folder

import os

class Config:
    """Config class"""
    SECRET_KEY: str = "46373hdnsfshf73462twvdngnghjdgsfd" #change for a secure random key
    BASE_PATH: str = os.path.dirname(__file__)
    DEBUG: bool = True
    HOST: str = "localhost
    PORT: int = 8080
    LIFESPAN: str = "on"
```

The application can also be configered with a dictionary

```
app.configure_app({})
```

Available configuration options of the application are:

```
APP_NAME: str = "PyJolt"
VERSION: str = "1.0"
LOGGER_NAME: str = "PyJolt_logger"
TEMPLATES_DIR: str = "/templates" #directory with templates
STATIC_DIR: str = "/static" #folder for static assets/files
STATIC_URL: str = "/static" #url for static assets/files serving
TEMPLATES_STRICT: bool = True
STRICT_SLASHES: bool = False
OPEN_API: bool = True
OPEN_API_URL: str = "/openapi"
OPEN_API_DESCRIPTION: str = "Simple API"
```

You can then run the app with a run script:

```
#run.py <-- in the root folder

if __name__ == "__main__":
    import uvicorn
    from app.configs import Config
    uvicorn.run("app:create_app", host=Config.HOST, port=Config.PORT, lifespan=Config.LIFESPAN, reload=Config.DEBUG, factory=True)
```

```sh
uv run run.py
```

or directly from the terminal with:

```sh
uv run uvicorn app:create_app --reload --port 8080 --factory --host localhost
```

This will start the application on localhost on port 8080 with reload enabled (debug mode). The **lifespan** argument is important when you wish to use a database connection or other on_startup/on_shutdown methods. If lifespan="on", uvicorn will give startup/shutdown signals which the app can use to run certain methods. Other lifespan options are: "auto" and "off".

##Adding controllers for request handling

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

The controller must be registered with the application in the factory function like this:

```
#app/__init__.py <-- in the app folder
.
.
.

def create_app(configs: Config) -> PyJolt:
    .
    .
    .
    from app.api.users.users_api import UserApi
    app.register_controller(UserApi)
    .
    .
    .
    return app
```

In the above example controller the **post** route accepts incomming json data (@consumes) and automatically
injects it into the **user_data** variable with a Pydantic BaseModel type object. The incomming data is also automatically validated
and raises a validation error (422 - Unprocessible entity) if data is incorrect/missing. For more details about data validation and options
we suggest you take a look at the Pydantic library. The @produces decorator automatically sets the correct content-type on the 
response object and the return type hint (-> Response[UserData]:) indicates as what type of object the response body should be serialized.

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

The above CustomExceptionHandler class can be registered with the application in the factory function with

```
from app.api.exceptions.exception_handler import CustomExceptionHandler
app.register_exception_handler(CustomExceptionHandler)
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

##Template responses

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

###Database connectivity and management

To add database connectivity to your PyJolt app you can use the database module.

```
#extensions.py
from pyjolt.database import SqlDatabase
from pyjolt.database.migrate import Migrate

db: SqlDatabase = SqlDatabase()
migrate: Migrate = Migrate()
```

you can then import and initilize the extensions in the factory method:

```
#__init__.py

def create_app(configs: Config) -> PyJolt:
    .
    .
    .
    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
```

This will initilize and configure the extensions with the application. To configure the extensions simply add
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

In both cases the extensions can be passed a variable prefix string when instantiated:
```
#extensions.py
.
.
.
db: SqlDatabase = SqlDatabase("MY_DB_")
migrate: Migrate = Migrate("MY_DB_")
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
from app import create_app

if __name__ == "__main__":
    app = create_app()
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

**The use of the Migrate extension is completely optional when using a database.**

### Database Models
To store/fetch data from the database you can use model classes. An example class is:

```
#app/api/models/user_model.py

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.extensions import db

class User(db.Model):
    """
    User model
    """
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(50), unique=True)
```

**For model detection (for correct Migration extension working) all models should be  imported into the factory method. Beware of circular imports. Order of imports can matter.**

**SqlDatabase and Migrate extension uses Sqlalchemy and Alembic under the hood.**

Models like this can be used in controller endpoints for storing/fetching like this:

```
@get("/<int:user_id>")
@produces(MediaType.TEXT_HTML)
async def get_user(self, req: Request, user_id: int) -> Response[UserData]:
    """Returns a user by user_id"""
    user: User = await User.query().filter_by(id=user_id).first()

    return req.response.json(UserData(id=user_id, fullname=user.fullname, email=user.email)).status(HttpStatus.OK)

@post("/")
@consumes(MediaType.APPLICATION_JSON)
@produces(MediaType.APPLICATION_JSON)
async def get_user(self, req: Request, user_data: UserData) -> Response[UserData]:
    """Creates new user"""
    user: User = User(fullname=user_data.fullname, email=user_data.email)
    session = db.create_session()
    session.add(user)
    await session.commit()

    return req.response.json(UserData(id=user_id, fullname=user.fullname)).status(HttpStatus.OK)
```

When performing a simple one-time query like in the above example db session creation is handled automatically by the .query() method of the model.
However, when performing multiple queries, adding/deleting records etc. it is recommended to create the session (like in the above POST example)
and pass it to the .query(session) methods. In this way, all queries will use the same session.

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

The Auth class inherits from the PyJolt Authentication class. The user must implement the user_loader and role_check methods.
These methods provide logic for loading a user when a protected endpoint is requested and checking if the user has permissions.
Above is an example which loads the user from a cookie. If the user is not found an AuthenticationException is raised which can be handled
in the CustomExceptionHandler. If the user doesn't have required roles (role_check -> False) an UnauthorizedException exception is raised
which can be also handled in the CustomExceptionHandler.

The instantiated Auth class can then be imported to the factory method and initilized with the application object.

```
#__init__.py

def create_app(configs: Config) -> PyJolt:
    .
    .
    .
    from app.authentication import auth
    auth.init_app(app)
```

Controller endpoints can be protected which two decorators like this:

```
@get("/<int:user_id>")
@produces(MediaType.TEXT_HTML)
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


