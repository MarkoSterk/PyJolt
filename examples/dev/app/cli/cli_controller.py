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
    
    @command("goodbye", help="Says goodbye")
    async def say_goodbye(self):
        """Say goodbye when the CLI exits."""
        print("Goodbye! Thanks for using the CLI utility.")
