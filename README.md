Data Extractor

Effortlessly extract structured data (names, emails, phone numbers, and more) from your PDF documents using AI. This project features a modern UI, dashboard, and supports batch PDF uploads.

---

## Features

- Upload single or multiple PDF files
- Extract names, emails, phone numbers, and more using AI (spaCy NER)
- Download results as CSV
- Interactive dashboard for data visualization
- Modern landing page and UI
- "How it works" modal for user guidance

---

## Project Structure

```
Data-Extractor/
├── api/
│   └── index.py         # Flask app entrypoint for Vercel
├── static/
│   └── Public/          # Background and logo images
│   └── ...              # Other static assets
├── templates/
│   ├── index.html       # Main extraction page
│   └── landing.html     # Landing page
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel deployment config
└── README.md            # This file
```

---

## Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Data-Extractor
   ```
2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
4. **Run the app locally:**
   ```bash
   python app.py
   ```
   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Deploying to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```
2. **Move Flask app to `api/index.py`:**
   ```bash
   mkdir api
   mv app.py api/index.py
   ```
   Remove or comment out `if __name__ == '__main__': ...` in `index.py`.
3. **Ensure your static and templates folders are at the project root.**
4. **Add a `vercel.json` file:**
   ```json
   {
     "version": 2,
     "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
     "routes": [
       { "src": "/static/(.*)", "dest": "/static/$1" },
       { "src": "/(.*)", "dest": "/api/index.py" }
     ]
   }
   ```
5. **Deploy:**
   ```bash
   vercel --prod
   ```
   Follow the prompts. Your app will be live at the provided Vercel URL.

---

## Notes

- Make sure your images are in `static/Public/` and referenced as `/static/Public/your-image.png`.
- For any issues, check the Vercel logs or open an issue in this repo.

---

## License

MIT
