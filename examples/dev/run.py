"""Run script for testg app"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:create_app", host="localhost", port=8080, lifespan="on", reload=True, factory=True)
