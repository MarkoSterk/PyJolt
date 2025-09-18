"""CLI utility script"""
from app import create_app


#Available cli command for db migrations
#Database models must be imported into the create_app factory function in order
#for the migration module to detect the correctly
#uv run cli.py db-init
#uv run cli.py db-migrate
#uv run cli.py db-upgrade

if __name__ == "__main__":
    ##CLI interface for application
    app = create_app()
    app.run_cli()
