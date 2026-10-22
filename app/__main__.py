from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    from app.config import config

    uvicorn.run("app.main:app", host="0.0.0.0", port=config.store.port, reload=False)
