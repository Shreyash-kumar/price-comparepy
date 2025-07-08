## Prerequisites
- Python 3.9+
- Vercel CLI (`npm install -g vercel`)

## Local Setup and Running
1. Clone the repository or create a project directory with `main.py`, `requirements.txt`, and `vercel.json`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
4. Test the API (e.g., using cURL):
   ```bash
   curl -X POST http://127.0.0.1:8000/search \
     -H "Content-Type: application/json" \
     -d '{"country": "IN", "query": "iPhone 16 256GB"}'
   ```

## Deploying to Vercel
1. Initialize the project:
   ```bash
   vercel
   ```
2. Follow prompts to set up and deploy.
3. Deploy to production:
   ```bash
   vercel --prod
   ```
4. Test the deployed API:
   ```bash
   curl -X POST https://price-compare-shreyash-kumar-shreyash-kumars-projects.vercel.app/search \
     -H "Content-Type: application/json" \
     -d '{"country": "IN", "query": "iPhone 16 256GB"}'
   ```

## Notes
- Ensure `requirements.txt` includes all dependencies.
- Check Vercel logs for issues: `vercel logs your-app.vercel.app`.
- Web scraping may face blocks; consider proxies or APIs for production.
