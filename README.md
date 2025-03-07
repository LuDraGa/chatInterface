**PROJECT SETUP**

1. git clone `<project_path>`
2. cd `<project_path>`
3. python3 -m venv venv
4. source activate venv venv
5. pip install uv
6. uv sync --active
7. chainlit create-secret
   1. <copy the secret to .env as directed>
   2. Add the azure openai service creds from the github marketplace(free) to .env
      1. AZURE_OPENAI_API_KEY
      2. AZURE_OPENAI_BASE_URL
8. DATA LAYER SETUP
   1. Steup 1(predone work)
      1. Already cloned the repo and setup with changes
      2. cd chainlit-datalayer
      3. docker compose up -d
      4. npx prisma migrate deploy
      5. npx prisma studio
   2. Setup 2 (from scratch): Follow [https://github.com/Chainlit/chainlit-datalayer](https://github.com/Chainlit/chainlit-datalayer)
      1. git clone from [https://github.com/Chainlit/chainlit-datalayer](https://github.com/Chainlit/chainlit-datalayer)
      2. cd chainlit-datalayer
      3. python3 -m venv data-layer
      4. source data-layer/bin/activate
      5. pip install asyncpg boto3
      6. cp .env.example .env [This is to just copy all env vars for datalayer]
      7. docker compose up -d
      8. npx prisma migrate deploy
      9. npx prisma studio
9. cd to <project_path>
10. chainlit run test_app.py
