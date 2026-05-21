## Local startup

docker compose up -d vault

uvicorn model_server.main:app --reload

uvicorn app.main:app --reload