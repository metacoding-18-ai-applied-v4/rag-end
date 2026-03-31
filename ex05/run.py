import os
import uvicorn

os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
