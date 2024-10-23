from fastapi import FastAPI
from src.Controller.BaseController import router as base_controller 
app = FastAPI()

# Include user API router
app.include_router(base_controller, prefix="/api")

@app.lifespan("startup")
async def startup_event():
    # Initialize database connection, etc.
    pass

@app.lifespan("shutdown")
async def shutdown_event():
    # Cleanup tasks (e.g., close DB connections)
    pass

# Run the application with:
# uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)  # Running on a different port