from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini API
print(os.getenv("GEMINI_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define profit calculation functions
def calculate_mudarabah_profit(total_profit, capital_provider_ratio):
    """
    Calculate profit distribution for Mudarabah contract
    
    In Mudarabah, one party (rab al-mal) provides capital, and the other (mudarib) 
    provides labor/expertise. Profits are shared according to pre-agreed ratios.
    """
    # Convert percentage to decimal
    capital_provider_ratio = float(capital_provider_ratio) / 100
    
    # Calculate shares
    capital_provider_share = total_profit * capital_provider_ratio
    mudarib_share = total_profit - capital_provider_share
    
    return {
        "capital_provider_share": round(capital_provider_share, 2),
        "mudarib_share": round(mudarib_share, 2),
        "profit_ratio": f"{capital_provider_ratio*100}:{(1-capital_provider_ratio)*100}"
    }

def calculate_musharakah_profit(total_profit, capital_contributions, profit_sharing_ratios=None):
    """
    Calculate profit distribution for Musharakah contract
    
    In Musharakah, all parties contribute capital and share profits according to 
    either their capital contribution ratio or pre-agreed profit-sharing ratios.
    """
    total_capital = sum(capital_contributions)
    shares = []
    
    # If profit sharing ratios are provided, use those
    if profit_sharing_ratios:
        # Normalize ratios to ensure they sum to 1
        total_ratio = sum(profit_sharing_ratios)
        normalized_ratios = [r/total_ratio for r in profit_sharing_ratios]
        
        for i, ratio in enumerate(normalized_ratios):
            partner_share = total_profit * ratio
            shares.append({
                "partner": i+1,
                "capital_contribution": capital_contributions[i],
                "capital_ratio": round(capital_contributions[i] / total_capital * 100, 2),
                "profit_share": round(partner_share, 2),
                "profit_ratio": round(ratio * 100, 2)
            })
    # Otherwise use capital contribution ratios
    else:
        for i, capital in enumerate(capital_contributions):
            ratio = capital / total_capital
            partner_share = total_profit * ratio
            shares.append({
                "partner": i+1,
                "capital_contribution": capital,
                "capital_ratio": round(ratio * 100, 2),
                "profit_share": round(partner_share, 2),
                "profit_ratio": round(ratio * 100, 2)
            })
    
    return shares

def get_explanation(contract_type, params):
    """Get explanation from Gemini API about the calculation methodology"""
    import requests
    
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Create your prompt based on contract_type and params
    if contract_type == "mudarabah":
        prompt = f"""
        As an Islamic finance expert, explain the profit distribution methodology for this Mudarabah contract.
        
        Contract details:
        - Total profit: {params['total_profit']}
        - Capital provider's profit ratio: {params['capital_provider_ratio']}%
        - Capital provider's share: {params['result']['capital_provider_share']}
        - Mudarib's share: {params['result']['mudarib_share']}
        
        IMPORTANT: Your response must be in properly formatted HTML that can be directly inserted into a webpage.
        DO NOT use markdown, backticks, or code blocks. Provide ONLY valid HTML.
        
        Structure your HTML response like this:
        
        <div class="explanation-content">
            <h4>What is a Mudarabah Contract?</h4>
            <p>Explanation here...</p>
            
            <h4>Profit Distribution Calculation</h4>
            <p>In this scenario, calculation explanation...</p>
            
            <h4>Islamic Finance Principles and AAOIFI Alignment</h4>
            <p>Explanation of how this aligns with principles...</p>
        </div>
        
        Make it concise (under 250 words), educational, and easy for non-experts to understand.
        """
    else:  # musharakah
        partners_info = "\n".join([
            f"- Partner {item['partner']}: Contributed {item['capital_contribution']} ({item['capital_ratio']}% of capital), " +
            f"Receiving {item['profit_share']} ({item['profit_ratio']}% of profits)"
            for item in params['result']
        ])
        
        prompt = f"""
        As an Islamic finance expert, explain the profit distribution methodology for this Musharakah contract.
        
        Contract details:
        - Total profit: {params['total_profit']}
        - Total capital: {sum(params['capital_contributions'])}
        - Partners' details:
        {partners_info}
        
        IMPORTANT: Your response must be in properly formatted HTML that can be directly inserted into a webpage.
        DO NOT use markdown, backticks, or code blocks. Provide ONLY valid HTML.
        
        Structure your HTML response like this:
        
        <div class="explanation-content">
            <h4>What is a Musharakah Contract?</h4>
            <p>Explanation here...</p>
            
            <h4>Profit Distribution Calculation</h4>
            <p>In this scenario, calculation explanation...</p>
            
            <h4>Islamic Finance Principles and AAOIFI Alignment</h4>
            <p>Explanation of how this aligns with principles...</p>
        </div>
        
        Make it concise (under 250 words), educational, and easy for non-experts to understand.
        """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        result = response.json()
        
        # Extract the text from the response
        if "candidates" in result and result["candidates"]:
            raw_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean the response - remove any code blocks or markdown formatting
            # If the response is wrapped in ```html ``` or similar, extract just the HTML
            if "```html" in raw_response:
                raw_response = raw_response.split("```html")[1].split("```")[0].strip()
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0].strip()
                
            return raw_response
        else:
            return "<p>No explanation available</p>"
    except Exception as e:
        print(f"Direct API Error: {str(e)}")
        return f"<p>Unable to generate explanation: {str(e)}</p>"
    
# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    contract_type = data['contract_type']
    
    try:
        if contract_type == 'mudarabah':
            total_profit = float(data['total_profit'])
            capital_provider_ratio = float(data['capital_provider_ratio'])
            
            result = calculate_mudarabah_profit(total_profit, capital_provider_ratio)
            
            # Get explanation from Gemini
            explanation = get_explanation('mudarabah', {
                'total_profit': total_profit,
                'capital_provider_ratio': capital_provider_ratio,
                'result': result
            })
            
            return jsonify({
                'success': True,
                'result': result,
                'explanation': explanation
            })
            
        elif contract_type == 'musharakah':
            total_profit = float(data['total_profit'])
            capital_contributions = [float(c) for c in data['capital_contributions']]
            
            # Check if custom profit sharing ratios are provided
            profit_sharing_ratios = None
            if 'profit_sharing_ratios' in data and data['profit_sharing_ratios']:
                profit_sharing_ratios = [float(r) for r in data['profit_sharing_ratios']]
            
            result = calculate_musharakah_profit(total_profit, capital_contributions, profit_sharing_ratios)
            
            # Get explanation from Gemini
            explanation = get_explanation('musharakah', {
                'total_profit': total_profit,
                'capital_contributions': capital_contributions,
                'result': result
            })
            
            return jsonify({
                'success': True,
                'result': result,
                'explanation': explanation
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid contract type'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5501)