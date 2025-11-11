"""
Simple run script
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="app:App",
        host="localhost",
        port=8080,
        lifespan="on",
        reload=True,
        factory=True
    )
