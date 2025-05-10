# Islamic Profit Calculator

A simple web app to calculate profit distributions based on Islamic finance contracts: **Mudarabah** and **Musharakah** with AI for explanation

---

## Installation Guide

1. **Clone the repository**

```bash
git clone https://github.com/MohammedChakerBaaziz/Islamic-Profit-Calculator.git
cd Islamic-Profit-Calculator
````

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, run:

```bash
pip install flask flask-cors python-dotenv google-generativeai
```

4. **Add your Gemini API key**

Create a `.env` file and add:

```
GEMINI_API_KEY=your_google_gemini_api_key_here
```

---

## Run the app

```bash
python app.py
```

The backend will run on: [http://localhost:9937](http://localhost:9937)

Open `index.html` in your browser to use the app.

---

## Files

* `app.py` – Flask backend
* `index.html` – Frontend UI
* `.env` – Your Gemini API key (not included in Git)
* `requirements.txt` - Necessary packages for the backend

