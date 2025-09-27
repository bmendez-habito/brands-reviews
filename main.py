import uvicorn
from src.utils.config import settings

def main():
    uvicorn.run("src.web.app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

if __name__ == "__main__":
    main()
