# EduBridge-AI deployment guide

## Important: use Streamlit Community Cloud, not GitHub Pages

This project is a Python/Streamlit application. GitHub Pages only hosts static files (HTML/CSS/JavaScript), so it cannot run `app.py`.

## Deploy

1. Extract this ZIP.
2. Upload the contents of the extracted folder to your GitHub repository. Ensure `app.py` and `requirements.txt` are at the repository root.
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Choose **Create app**, select your repository and branch (`main`), and set **Main file path** to `app.py`.
5. Deploy the app.
6. In the Streamlit app dashboard, open **App settings → Secrets** and add only the credentials you actually use. Use TOML format, for example:

```toml
APP_BASE_URL = "https://YOUR-APP-NAME.streamlit.app"
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
GITHUB_CLIENT_ID = "your-github-client-id"
GITHUB_CLIENT_SECRET = "your-github-client-secret"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
```

Do not paste real credentials into GitHub, source files, screenshots, or chat. Leave out unused settings. Configure the matching OAuth redirect/callback URLs in the Google/GitHub provider consoles using the exact callback URL documented in `GOOGLE_SETUP.md`.

## Local Windows test

Open PowerShell in the folder containing `app.py` and run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important data note

The app uses a local SQLite database (`edubridge.db`). On hosted platforms, local files may not be durable across rebuilds/restarts. For real multi-user use, migrate the database to a persistent hosted database and configure backups.

## Project structure

`app.py` is at the ZIP root, alongside `requirements.txt`; supporting Python modules and `auth_component/` are included.
