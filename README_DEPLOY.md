# Deploying MegaGrok Graphics Bot to Render

1. Create a new Web Service in Render (or a Background Worker with a web/health endpoint).
2. Connect your Git repo or upload these files.
3. Set Environment Variables (in Render dashboard):

   - OPENAI_API_KEY = <your-openai-api-key>
   - TELEGRAM_BOT_TOKEN = <your-telegram-bot-token>
   - TELEGRAM_CHAT_ID = <your_group_chat_id>   # negative numbers for supergroups/channels
   - POST_INTERVAL_HOURS = 2                    # default: 2
   - IMAGE_SIZE = 1024x1024
   - IMAGE_FORMAT = png

4. Build Command: `pip install -r requirements.txt`
   Start Command: `gunicorn main:app --workers 1 --threads 4 --timeout 120`
   (Or use the provided Procfile/start.sh)

5. Deploy. The service will run and post the first image immediately, then every POST_INTERVAL_HOURS.

6. Logs: Check Render logs to view generation activity and troubleshooting.

Notes:
- On first run the bot sends one initial image. If you'd like to disable that, remove the initial job call.
- You can provide a MOBS JSON file via env var MOBS_JSON_PATH to change the mob roster without redeploy.
