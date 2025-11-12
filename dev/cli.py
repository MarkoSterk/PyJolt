"""
CLI script
"""

if __name__ == "__main__":
    from app import App
    app: App = App(cli_mode=True)
    app.run_cli()
