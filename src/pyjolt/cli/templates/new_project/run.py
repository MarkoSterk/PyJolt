"""Run script for testg app"""

if __name__ == "__main__":
    import uvicorn
    from app.configs import Config
    ##Change parameters for starting the app (host, port etc)
    ##reload=True -> watches for file changes and reloads.
    uvicorn.run("app:create_app", host=Config.HOST, port=Config.PORT,
                lifespan=Config.LIFESPAN, reload=Config.DEBUG, factory=True)
