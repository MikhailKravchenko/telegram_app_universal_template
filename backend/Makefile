.PHONY: test test-accounts test-api test-services test-tasks test-coverage test-unit test-integration

init: init-envs pre-commit
init-envs:
	cp env.example .env
	cp config.example.yaml config.yaml

# Основные команды тестирования
test:
	sudo docker-compose -f test.yml up --build --abort-on-container-exit

# Тестирование приложения accounts
test-accounts:
	python -m pytest tests/accounts/ -v --tb=short

# Тестирование только API endpoints
test-api:
	python -m pytest tests/accounts/api/ -v --tb=short -m api

# Тестирование только сервисов
test-services:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/services/ -v --tb=short -m unit

# Тестирование только задач
test-tasks:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/tasks/ -v --tb=short -m task

# Тестирование с покрытием кода
test-coverage:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/ --cov=src/accounts --cov-report=html --cov-report=term-missing

# Только unit тесты
test-unit:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/ -v --tb=short -m "unit"

# Только интеграционные тесты
test-integration:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/ -v --tb=short -m "integration"

# Быстрые тесты (без медленных)
test-fast:
	source .venv/bin/activate.fish && python -m pytest tests/accounts/ -v --tb=short -m "not slow"

# Тестирование конкретного файла
test-file:
	@read -p "Введите путь к файлу: " file; \
	source .venv/bin/activate.fish && python -m pytest $$file -v --tb=short

build:
	sudo docker-compose up --build -d 

full-migrate: makemigrations migrate
makemigrations:
	sudo docker-compose exec web ./manage.py makemigrations
migrate:
	sudo docker-compose exec web ./manage.py migrate

shell:
	sudo docker-compose exec web ./manage.py shell_plus
collectstatic:
	sudo docker-compose exec web ./manage.py collectstatic
admin:
	sudo docker-compose exec web ./manage.py createsuperuser
web-logs:
	sudo docker-compose logs -f web

pre-commit:
	pip install pre-commit --upgrade
	pre-commit install
