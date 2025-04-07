import uvicorn

if __name__ == "__main__":
    # The server port was intentionally changed from 8000 to 5000 for integration purposes.
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)

