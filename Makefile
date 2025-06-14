# 開発サーバ起動系
server-up:
	cd server && docker compose up

front-up:
	cd frontend && yarn dev

# フロントフォーマット系

front-format:
	cd frontend && yarn format --write

front-lint:
	cd frontend && yarn lint

front-test:
	cd frontend && yarn test

front-tsc:
	cd frontend && yarn tsc

# サーバフォーマット系

server-format:
	cd server && docker compose exec api uv run ruff format

server-lint:
	cd server && docker compose exec api uv run ruff check

server-test:
	cd server && docker compose exec api uv run pytest
