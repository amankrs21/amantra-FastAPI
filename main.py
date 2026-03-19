"""
THIS CODE IS ONLY FOR DEVELOPMENT PURPOSES, NOT FOR PRODUCTION
It is used to run the FastAPI app with uvicorn for development and testing.
"""

from __future__ import annotations

import os


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")  # noqa: S104
    uvicorn.run("src.app:app", host=host, port=8000, reload=True)
