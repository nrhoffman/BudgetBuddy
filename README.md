# BudgetBuddy

python -m uvicorn app.main:app --reload --port 8001

npm run dev

ngrok http 8001

redis-server

python -m celery -A app.celery_app worker -l info -P solo 
