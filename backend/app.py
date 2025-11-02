from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import logging
import json
from company_research import CompanyResearch
from job_analyzer import JobAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Allow CORS from extension and localhost during development. Using a permissive
# origin here makes development easier (the extension origin can vary). If
# deploying to production lock this down to the exact extension id or domain.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize NLP components
try:
    nlp = spacy.load("en_core_web_md")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

job_analyzer = JobAnalyzer(nlp)
company_researcher = CompanyResearch()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Inclusive Job Search API is running'
    })

@app.route('/analyze', methods=['POST'])
def analyze_job():
    try:
        data = request.json
        if not data:
            logger.error("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400
            
        logger.info(f"Received request data: {json.dumps(data, indent=2)}")
            
        job_description = data.get('description', '')
        company_name = data.get('company', '')
        user_skills = data.get('skills', [])
        
        logger.info(f"Extracted fields - Company: {company_name}, Skills: {user_skills}")
        
        logger.info(f"Received analysis request for company: {company_name}")
        logger.debug(f"Job description length: {len(job_description)}")
        
        if not job_description or not company_name:
            logger.error("Missing required fields")
            return jsonify({'error': 'Job description and company name are required'}), 400
        
        # Analyze job description with user's skills
        logger.info("Starting job analysis")
        skills_analysis = job_analyzer.analyze(job_description, user_skills)
        
        # Research company culture
        company_analysis = company_researcher.research(company_name)
        
        # Log match calculation for debugging
        logger.info(f"Match calculation: {skills_analysis.get('matchPercentage')}% match with user skills: {user_skills}")
        
        return jsonify({
            'simplified_description': skills_analysis.get('simplified_description', ''),
            'skills': skills_analysis.get('skills', []),
            'matchPercentage': skills_analysis.get('matchPercentage', 0),
            'inclusionScore': company_analysis['inclusion_score'],
            'supportPrograms': company_analysis['support_programs']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)