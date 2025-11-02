import spacy
from typing import Dict, List
import re

from skills_extractor import SkillsExtractor

class JobAnalyzer:
    def __init__(self, nlp):
        self.nlp = nlp
        self.skills_extractor = SkillsExtractor()
        # Initialize technical terms dictionary used by simplify_technical_terms
        # This will be extended later in the method with more human-friendly
        # explanations.
        self.technical_terms = {}
    
    def simplify_technical_terms(self, text: str) -> str:
        doc = self.nlp(text)
        simplified_text = text
        
        # Enhanced technical terms dictionary with neurodivergent-friendly explanations
        enhanced_terms = {
            "frontend development": "creating the parts of websites and apps that you can see and interact with directly, like buttons and menus",
            "backend development": "building the behind-the-scenes systems that make websites and apps work, like saving your information",
            "full-stack": "being able to work on both the visible parts of websites/apps AND the behind-the-scenes systems",
            "API": "a set of rules that lets different computer programs talk to each other, like how apps on your phone can share information",
            "cloud computing": "using computers that are somewhere else on the internet instead of your own computer",
            "agile methodology": "a way of working where big projects are broken down into smaller, manageable pieces",
            "REST API": "a standard way for web programs to send and receive information, like how your weather app gets updates",
            "database": "a digital filing cabinet where information is stored and organized",
            "version control": "keeping track of all changes made to code, like having an undo button for everything",
            "deployment": "the process of making a website or app available for people to use",
            "debugging": "finding and fixing problems in code, like being a detective",
            "UI/UX": "making websites and apps easy and enjoyable to use",
            "scalable": "able to handle more people using it without slowing down or breaking",
            "optimization": "making something work faster and better",
            "framework": "a pre-built set of tools that makes creating websites or apps easier",
            "implementation": "turning an idea into a real, working program",
            "JavaScript": "a programming language that makes websites interactive",
            "TypeScript": "a more organized version of JavaScript that helps catch mistakes early",
            "React": "a tool for building website interfaces that respond quickly to user actions",
            "Node.js": "a way to use JavaScript for backend (behind-the-scenes) programming",
            "AWS": "Amazon's cloud computing service that provides internet-based computing resources",
            "Azure": "Microsoft's cloud computing service, similar to AWS",
            "agile": "a flexible way of working where tasks are broken into small, manageable pieces"
        }
        
        # Add the terms to the original dictionary
        self.technical_terms.update(enhanced_terms)
        
        # First pass: Replace technical terms with explanations
        for term, explanation in self.technical_terms.items():
            pattern = rf"\b{term}\b"
            if term.lower() in text.lower():
                simplified_text = re.sub(
                    pattern,
                    f"{term} (simplified: {explanation})",
                    simplified_text,
                    flags=re.IGNORECASE
                )
        
        # Second pass: Break down complex sentences
        sentences = []
        for sent in doc.sents:
            if len(sent) > 20:  # If sentence is long
                # Try to break it at logical points
                parts = str(sent).split(', ')
                # Clean up the parts
                parts = [p.strip() for p in parts]
                sentences.extend(parts)
            else:
                sentences.append(str(sent))
        
        return ' '.join(sentences)
    
    def extract_skills(self, text: str) -> List[str]:
        doc = self.nlp(text)
        skills = set()
        
        # Common technical skills and frameworks to look for
        technical_skills = {
            "programming": ["python", "java", "javascript", "typescript", "c++", "ruby", "php", "swift", "kotlin", "rust", "go"],
            "web": ["html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "restful", "api", "rest"],
            "database": ["sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
            "tools": ["git", "jenkins", "jira", "agile", "scrum"],
            "methodologies": ["agile", "scrum", "waterfall", "kanban", "devops"]
        }
        
        # Extract skills based on key phrases and patterns
        skill_patterns = [
            "experience in",
            "knowledge of",
            "proficient in",
            "familiar with",
            "expertise in",
            "skills in",
            "background in",
            "working with",
            "understanding of"
        ]
        
        # Clean up function for skills
        def clean_skill(skill: str) -> str:
            # Remove common unnecessary words and punctuation
            skill = skill.lower().strip()
            skill = skill.split(" and ")[0]  # Take first part if "and" is present
            skill = skill.split(" or ")[0]   # Take first part if "or" is present
            skill = skill.split(" is ")[0]   # Remove anything after "is"
            skill = skill.rstrip(".,")       # Remove trailing punctuation
            return skill

        # Find skills based on patterns
        for sentence in doc.sents:
            sent_lower = sentence.text.lower()
            for pattern in skill_patterns:
                if pattern in sent_lower:
                    # Extract the relevant part after the pattern
                    skill_text = sent_lower.split(pattern)[1].strip()
                    # Split by common delimiters
                    sub_skills = [s.strip() for s in skill_text.split(',')]
                    for sub_skill in sub_skills:
                        cleaned = clean_skill(sub_skill)
                        if len(cleaned) > 2:  # Avoid single letters or empty strings
                            skills.add(cleaned)

        # Find technical skills
        text_lower = text.lower()
        for category, skill_list in technical_skills.items():
            for skill in skill_list:
                # Check for exact word boundaries
                if f" {skill} " in f" {text_lower} ":
                    skills.add(skill)
                # Special cases for common variations
                if skill == "react" and "react.js" in text_lower:
                    skills.add("react")
                if skill == "node.js" and "nodejs" in text_lower:
                    skills.add("node.js")

        # Clean up and normalize skills
        normalized_skills = set()
        for skill in skills:
            # Normalize some common variations
            if "react" in skill.lower():
                normalized_skills.add("react")
            elif "node" in skill.lower():
                normalized_skills.add("node.js")
            elif any(api in skill.lower() for api in ["rest", "restful", "api"]):
                normalized_skills.add("restful api")
            elif any(term in skill.lower() for term in ["aws", "azure", "cloud"]):
                if "aws" in skill.lower():
                    normalized_skills.add("aws")
                if "azure" in skill.lower():
                    normalized_skills.add("azure")
            else:
                normalized_skills.add(skill)

        return sorted(list(normalized_skills))
    
    def calculate_match_percentage(self, required_skills: List[str], user_skills: List[str] = None) -> int:
        """Calculate the match percentage between required and user skills.
        
        The percentage is calculated as:
        (number of matching skills) / (total number of required skills) * 100
        """
        if not user_skills:
            print("No user skills provided")
            return 0
        
        # Convert all skills to lowercase for case-insensitive comparison
        required_lower = [skill.lower() for skill in required_skills]
        user_lower = [skill.lower() for skill in user_skills]
        
        # Track matching skills for logging
        matching_skills = []
        for user_skill in user_lower:
            for req_skill in required_lower:
                if user_skill in req_skill or req_skill in user_skill:
                    matching_skills.append((user_skill, req_skill))
                    break  # Count each user skill only once
        
        # Calculate percentage
        if not required_skills:
            print("No required skills found")
            return 0
            
        match_percent = int((len(matching_skills) / len(required_skills)) * 100)
        
        # Detailed logging
        print("\nSkill Matching Details:")
        print(f"User skills: {user_skills}")
        print(f"Required skills: {required_skills}")
        print("\nMatched pairs:")
        for user, req in matching_skills:
            print(f"User skill '{user}' matches required skill '{req}'")
        print(f"\nMatch calculation: {len(matching_skills)} matching skills out of {len(required_skills)} required = {match_percent}%")
        
        return match_percent
    
    def analyze(self, job_description: str, user_skills: List[str] = None) -> Dict:
        """Analyze a job description using LLM and compare with user skills."""
        # Extract skills (may be list of dicts {'name','category'} or simple strings)
        skills_data = self.skills_extractor.extract_skills(job_description)

        # Normalize to a list of skill names
        required_skills = []
        if isinstance(skills_data, list):
            for s in skills_data:
                if isinstance(s, dict):
                    name = s.get('name') or s.get('skill') or ''
                    if name:
                        required_skills.append(name)
                elif isinstance(s, str):
                    required_skills.append(s)

        # Deduplicate and clean
        required_skills = sorted(list(dict.fromkeys([sk.strip() for sk in required_skills if sk])))

        # Compute a match percentage using user's skills if provided
        match_percentage = self.calculate_match_percentage(required_skills, user_skills)

        simplified_description = self.simplify_technical_terms(job_description)

        return {
            'simplified_description': simplified_description,
            'skills': required_skills,
            'matchPercentage': match_percentage
        }