"""
User management CLI
"""
from pyjolt.cli import CLIController, command, argument
from pyjolt.database.sql import AsyncSession
from pyjolt.auth import AuthUtils

from app.extensions import db
from app.api.schemas.user_schemas import UserRegisterSchema
from app.api.models.user import User

class UserManagamentCli(CLIController):
    """
    Methods for user management
    """
    @command("add-user", help="Add a new user")
    @argument("email", arg_type=str, description="User email")
    @argument("fullname", arg_type=str, description="User fullname")
    @argument("password", arg_type=str, description="User password")
    @argument("confirm_password", arg_type=str, description="Confirm user password")
    @db.managed_session_for_cli
    #pylint: disable-next=R0913,R0917
    async def add_user(self, email: str, fullname: str,
                       password: str, confirm_password: str,
                       session: AsyncSession):
        """
        Adds a new user
        """
        user_data = UserRegisterSchema.model_validate({
            "email": email,
            "fullname": fullname,
            "password": password,
            "confirm_password": confirm_password
        }).model_dump()
        if user_data["password"] != user_data["confirm_password"]:
            #pylint: disable-next=W0719
            raise Exception("Password and confirm password must match")
        pass_hash: str = AuthUtils.create_password_hash(password)
        user: User = User(email=email,
                          fullname=fullname,
                          password=pass_hash) # type: ignore
        session.add(user)

        print("User added successfully")
