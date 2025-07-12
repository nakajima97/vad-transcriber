.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# 開発サーバ起動系
server-up:  ## サーバの開発環境起動
	cd server && docker compose up

front-up:  ## フロントの開発環境起動
	cd frontend && yarn dev

# フロントフォーマット系

front-format:  ## フロントのフォーマッター実行
	cd frontend && yarn format --write

front-lint:  ## フロントのリント実行
	cd frontend && yarn lint

front-test:  ## フロントのテスト実行
	cd frontend && yarn test

front-tsc:  ## フロントの型チェック実行
	cd frontend && yarn tsc

# サーバフォーマット系

server-format:  ## サーバーのフォーマッター実行
	cd server && docker compose exec api uv run ruff format

server-lint:  ## サーバーのリント実行
	cd server && docker compose exec api uv run ruff check

server-lint-fix:  ## サーバーのリント実行（自動修正の実行）
	cd server && docker compose exec api uv run ruff check --fix

server-test:  ## サーバーのテスト実行
	cd server && docker compose exec api env TESTING=true uv run pytest
