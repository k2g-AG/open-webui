@echo off
docker ps --format "{{.Names}}" | findstr /i /c:"postgres" > nul
if %errorlevel% neq 0 (
    echo Container postgres is not running. Starting it now...
    docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e PGDATA=/var/lib/postgresql/data/pgdata -v E:\Projects\bitbucket\open-webui\pipelines\tmp\postgresql:/var/lib/postgresql/data -p 5432:5432 postgres
) else (
    echo Container postgres is already running.
)

docker rm -f open-webui-docker-dev2
docker rmi -f open-webui-docker-dev2
docker build -t open-webui-docker-dev2 .
@REM docker run -d -p 3000:8080 -v E:\Projects\bitbucket\open-webui\pipelines\tmp\mount\open-webui:/app/backend/data -e DATABASE_URL=postgresql://postgres:postgres@192.168.188.232/postgres --name open-webui-docker-dev2 open-webui-docker-dev2
docker run -d -p 3000:8080 -v E:\Projects\bitbucket\open-webui\pipelines\tmp\mount\open-webui:/app/backend/data -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal/postgres --name open-webui-docker-dev2 open-webui-docker-dev2