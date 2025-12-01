import pdfplumber
import json
import re
from typing import List, Dict, Optional
from io import BytesIO
import ollama
from collections import defaultdict
import random


class ResumeAnalyzer:
    def __init__(self, question_bank_path: str, ollama_model: str = "llama3.2"):
        """Initialize the analyzer with a skill-question bank."""
        with open(question_bank_path, 'r') as f:
            self.question_bank = json.load(f)
        
        self.ollama_model = ollama_model
        self.use_ollama = self._check_ollama_available()  # Check if Ollama is available
        
        # Track question usage for rotation
        # Format: {(skill, level): [list of used question indices]}
        self.question_usage = defaultdict(list)
        
        # Build skill vocabulary mapping for fallback and validation
        self.skill_vocab = {}
        self.skill_keys = set()  # All available skill keys
        for entry in self.question_bank:
            skill_key = entry["skill"]
            display_name = entry["displayName"]
            self.skill_keys.add(skill_key)
            # Map variations to canonical key
            self.skill_vocab[skill_key.lower()] = skill_key
            self.skill_vocab[display_name.lower()] = skill_key
            # Add common variations
            if skill_key == "python":
                self.skill_vocab["python3"] = skill_key
                self.skill_vocab["python 3"] = skill_key
            elif skill_key == "javascript":
                self.skill_vocab["js"] = skill_key
                self.skill_vocab["node"] = skill_key
            elif skill_key == "nodejs":
                self.skill_vocab["node.js"] = skill_key
                self.skill_vocab["node"] = skill_key
        
        # Job role skill priorities
        self.job_role_priorities = {
            "data science": ["python", "sql", "javascript"],
            "software engineer": ["python", "javascript", "react", "nodejs"],
            "web developer": ["html", "css", "javascript", "react"],
            "backend developer": ["python", "nodejs", "sql"],
            "frontend developer": ["html", "css", "javascript", "react"]
        }
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available and the model exists."""
        try:
            # Try to list models to check if Ollama is running
            models = ollama.list()
            model_names = [model['name'] for model in models.get('models', [])]
            
            # Check if our model is available
            if self.ollama_model in model_names:
                return True
            
            # Try to use the model anyway (it might pull it automatically)
            # But for now, just return True if Ollama is running
            return len(model_names) > 0
        except Exception as e:
            print(f"Ollama not available: {str(e)}. Falling back to manual detection.")
            return False
    
    def extract_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for skill detection."""
        # Convert to lowercase and normalize whitespace
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def detect_skills_with_ollama(self, text: str, job_role: Optional[str] = None) -> List[Dict]:
        """Use Ollama to dynamically detect skills from resume text."""
        try:
            # Create a list of available skills for the AI to reference
            available_skills = [entry["skill"] for entry in self.question_bank]
            skills_list = ", ".join(available_skills)
            
            # Build prompt for skill detection
            # Limit text to avoid token limits
            resume_snippet = text[:3000]
            job_role_text = job_role if job_role else "none"
            
            prompt = f"""Analyze the following resume text and identify technical skills that match these available skills: {skills_list}

Resume text:
{resume_snippet}

For each skill you detect, provide:
1. The skill name (must match one of the available skills exactly: {skills_list})
2. The proficiency level: beginner, intermediate, or advanced
3. Brief context from the resume that supports your assessment

Return your response as a JSON array with this format:
[
  {{"skill": "python", "level": "advanced", "context": "brief context"}},
  {{"skill": "git", "level": "intermediate", "context": "brief context"}}
]

Only include skills that are clearly mentioned or implied in the resume. If a job role is specified ({job_role_text}), prioritize skills relevant to that role.

Return ONLY valid JSON, no additional text."""
            
            # Call Ollama
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical resume analyzer. You identify technical skills and assess proficiency levels from resume text. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            response_text = response['message']['content'].strip()
            
            # Extract JSON from response (handle cases where there's extra text)
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            detected_skills_data = json.loads(response_text)
            
            # Convert to our format and validate against question bank
            detected = []
            question_bank_dict = {e["skill"]: e for e in self.question_bank}
            
            for item in detected_skills_data:
                skill_key = item.get("skill", "").lower()
                level = item.get("level", "intermediate").lower()
                
                # Find matching skill in question bank (case-insensitive)
                matched_key = None
                for qb_skill in self.skill_keys:
                    if qb_skill.lower() == skill_key:
                        matched_key = qb_skill
                        break
                
                if matched_key and matched_key in question_bank_dict:
                    # Normalize level
                    if level not in ["beginner", "intermediate", "advanced"]:
                        level = "intermediate"
                    
                    display_name = question_bank_dict[matched_key]["displayName"]
                    detected.append({
                        "key": matched_key,
                        "name": display_name,
                        "level": level,
                        "context": item.get("context", "")
                    })
            
            return detected
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Ollama JSON response: {str(e)}, falling back to manual detection")
            return None
        except Exception as e:
            print(f"Ollama skill detection failed: {str(e)}, falling back to manual detection")
            return None
    
    def detect_skills(self, text: str, job_role: Optional[str] = None) -> List[Dict]:
        """Detect skills from resume text using AI, with fallback to manual detection."""
        # Try AI-based detection first
        if self.use_ollama:
            ai_detected = self.detect_skills_with_ollama(text, job_role)
            if ai_detected:
                # Prioritize by job role if provided
                if job_role:
                    job_role_lower = job_role.lower()
                    for role, skills in self.job_role_priorities.items():
                        if role in job_role_lower:
                            prioritized = []
                            for priority_skill in skills:
                                for skill in ai_detected:
                                    if skill["key"] == priority_skill and skill not in prioritized:
                                        prioritized.append(skill)
                            for skill in ai_detected:
                                if skill not in prioritized:
                                    prioritized.append(skill)
                            return prioritized
                return ai_detected
        
        # Fallback to manual detection
        normalized_text = self.normalize_text(text)
        detected = []
        
        # Check each skill in vocabulary
        for variant, canonical_key in self.skill_vocab.items():
            if variant in normalized_text:
                # Check if we already have this skill
                if not any(s["key"] == canonical_key for s in detected):
                    # Find display name
                    display_name = next(
                        (e["displayName"] for e in self.question_bank if e["skill"] == canonical_key),
                        canonical_key.capitalize()
                    )
                    detected.append({
                        "key": canonical_key,
                        "name": display_name,
                        "variant": variant
                    })
        
        # Infer skill levels using AI or fallback
        for skill in detected:
            skill["level"] = self.infer_skill_level(text, skill["key"], skill.get("variant", skill["key"]))
        
        # Prioritize by job role if provided
        if job_role:
            job_role_lower = job_role.lower()
            for role, skills in self.job_role_priorities.items():
                if role in job_role_lower:
                    prioritized = []
                    for priority_skill in skills:
                        for skill in detected:
                            if skill["key"] == priority_skill and skill not in prioritized:
                                prioritized.append(skill)
                    for skill in detected:
                        if skill not in prioritized:
                            prioritized.append(skill)
                    detected = prioritized
                    break
        
        return detected
    
    def infer_skill_level_with_ollama(self, text: str, skill_key: str) -> str:
        """Use Ollama to dynamically infer skill proficiency level from context."""
        try:
            # Find context around skill mentions
            pattern = rf'\b{re.escape(skill_key)}\b'
            matches = list(re.finditer(pattern, text.lower()))
            
            if not matches:
                return "intermediate"
            
            # Get context around skill mentions
            contexts = []
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                contexts.append(text[start:end])
            
            context_text = "\n\n---\n\n".join(contexts[:3])  # Limit to 3 contexts
            
            prompt = f"""Analyze the following resume excerpts that mention the skill "{skill_key}" and determine the proficiency level.

Resume excerpts:
{context_text}

Based on the context, experience descriptions, years of experience, project complexity, and language used, determine if the proficiency level is:
- "beginner": Basic knowledge, learning, introductory experience, familiar with
- "intermediate": Proficient, comfortable, 2-4 years experience, working knowledge
- "advanced": Expert, senior level, 5+ years, deep expertise, lead/architect experience

Respond with ONLY one word: "beginner", "intermediate", or "advanced"."""
            
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical recruiter analyzing skill proficiency levels. Respond with only one word: beginner, intermediate, or advanced."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            level = response['message']['content'].strip().lower()
            
            # Validate and normalize
            if level in ["beginner", "intermediate", "advanced"]:
                return level
            else:
                return "intermediate"
                
        except Exception as e:
            print(f"Ollama level inference failed for {skill_key}: {str(e)}, using fallback")
            return None
    
    def infer_skill_level(self, text: str, skill_key: str, variant: str) -> str:
        """Infer skill proficiency level from context using AI, with fallback to keyword matching."""
        # Try AI-based inference first
        if self.use_ollama:
            ai_level = self.infer_skill_level_with_ollama(text, skill_key)
            if ai_level:
                return ai_level
        
        # Fallback to keyword-based inference
        pattern = rf'\b{re.escape(variant)}\b'
        matches = list(re.finditer(pattern, text.lower()))
        
        if not matches:
            return "intermediate"  # default
        
        # Check context around each match
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].lower()
            
            # Advanced indicators
            advanced_keywords = [
                "advanced", "expert", "lead", "senior", "5+ years", "5 years",
                "extensive", "deep", "mastery", "proficient in", "experienced with"
            ]
            if any(kw in context for kw in advanced_keywords):
                return "advanced"
            
            # Beginner indicators
            beginner_keywords = [
                "beginner", "familiar", "some experience", "basic", "learning",
                "introduction", "introductory", "novice"
            ]
            if any(kw in context for kw in beginner_keywords):
                return "beginner"
            
            # Intermediate indicators
            intermediate_keywords = [
                "intermediate", "proficient", "2+ years", "2 years", "3+ years",
                "3 years", "comfortable", "working knowledge"
            ]
            if any(kw in context for kw in intermediate_keywords):
                return "intermediate"
        
        # Default to intermediate if no clear signal
        return "intermediate"
    
    def generate_questions_with_ollama(self, detected_skills: List[Dict], resume_text: str) -> List[Dict]:
        """Use Ollama to dynamically generate interview questions based on detected skills and levels."""
        try:
            questions = []
            
            # Get reference questions from bank to guide AI style
            question_bank_dict = {e["skill"]: e for e in self.question_bank}
            reference_examples = []
            
            for skill in detected_skills[:3]:  # Use first 3 skills for reference
                skill_key = skill["key"]
                if skill_key in question_bank_dict:
                    skill_entry = question_bank_dict[skill_key]
                    level = skill["level"]
                    # Get example questions for this level
                    level_questions = skill_entry["levels"].get(level, [])
                    if level_questions:
                        reference_examples.append({
                            "skill": skill_key,
                            "level": level,
                            "example": level_questions[0]
                        })
            
            # Build reference examples text
            examples_text = "\n".join([
                f'Skill: {ex["skill"]}, Level: {ex["level"]}, Example: "{ex["example"]}"'
                for ex in reference_examples
            ])
            
            # Create list of skills to generate questions for
            skills_to_question = []
            for skill in detected_skills:
                skill_key = skill["key"]
                level = skill["level"]
                display_name = skill["name"]
                context = skill.get("context", "")
                
                skills_to_question.append({
                    "skill": skill_key,
                    "displayName": display_name,
                    "level": level,
                    "context": context
                })
            
            skills_json = json.dumps(skills_to_question, indent=2)
            resume_snippet = resume_text[:2000]  # Limit resume text
            
            prompt = f"""You are a technical interviewer creating personalized interview questions based on a candidate's resume.

Reference question examples (to understand the style and difficulty):
{examples_text}

Candidate's detected skills and proficiency levels:
{skills_json}

Resume context (relevant excerpts):
{resume_snippet}

Generate 3-5 technical interview questions that:
1. Match the skill and proficiency level for each detected skill
2. Are personalized based on the resume context
3. Are appropriate for the stated proficiency level:
   - Beginner: Basic concepts, definitions, simple usage
   - Intermediate: Practical application, problem-solving, common patterns
   - Advanced: Complex scenarios, optimization, architecture, deep understanding
4. Are specific and technical (not generic "tell me about yourself" questions)

Return your response as a JSON array with this format:
[
  {{"skill": "python", "level": "advanced", "question": "Your generated question here"}},
  {{"skill": "git", "level": "intermediate", "question": "Your generated question here"}}
]

Generate questions for the top skills first. Return exactly 3-5 questions total.
Return ONLY valid JSON, no additional text."""
            
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer. You create personalized, level-appropriate technical interview questions based on resume analysis. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response['message']['content'].strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            generated_questions = json.loads(response_text)
            
            # Validate and format questions
            validated_questions = []
            question_bank_dict = {e["skill"]: e for e in self.question_bank}
            
            for item in generated_questions:
                skill_key = item.get("skill", "").lower()
                level = item.get("level", "intermediate").lower()
                question = item.get("question", "").strip()
                
                if not question:
                    continue
                
                # Find matching skill in question bank
                matched_key = None
                for qb_skill in self.skill_keys:
                    if qb_skill.lower() == skill_key:
                        matched_key = qb_skill
                        break
                
                if matched_key and matched_key in question_bank_dict:
                    # Normalize level
                    if level not in ["beginner", "intermediate", "advanced"]:
                        level = "intermediate"
                    
                    validated_questions.append({
                        "skill": matched_key,
                        "level": level,
                        "question": question
                    })
                    
                    if len(validated_questions) >= 5:
                        break
            
            return validated_questions[:5]
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Ollama question generation JSON: {str(e)}, using question bank")
            return None
        except Exception as e:
            print(f"Ollama question generation failed: {str(e)}, using question bank")
            return None
    
    def _get_next_question_from_bank(self, skill_key: str, level: str, exclude_question: Optional[str] = None) -> Optional[str]:
        """Get the next question from the question bank using rotation logic.
        
        Tracks question usage to avoid repeats until after ~10 uses.
        """
        question_bank_dict = {e["skill"]: e for e in self.question_bank}
        
        if skill_key not in question_bank_dict:
            return None
        
        skill_entry = question_bank_dict[skill_key]
        level_questions = skill_entry["levels"].get(level, [])
        
        if not level_questions:
            return None
        
        # Get usage tracking key
        usage_key = (skill_key, level)
        used_indices = self.question_usage[usage_key]
        
        MAX_REPEATS = 10  # Allow repeats after 10 uses
        
        # Filter out excluded question if provided
        available_indices = []
        for idx, question in enumerate(level_questions):
            # Skip if this is the excluded question
            if exclude_question and question == exclude_question:
                continue
            
            # Count how many times this question has been used in recent history
            recent_uses = used_indices[-MAX_REPEATS:].count(idx)
            
            # Include questions that haven't been used recently
            if recent_uses < MAX_REPEATS:
                available_indices.append((idx, question))
        
        # If all questions have been used recently, reset and allow all (except excluded)
        if not available_indices:
            available_indices = [
                (idx, q) for idx, q in enumerate(level_questions)
                if not exclude_question or q != exclude_question
            ]
            # Clear tracking after MAX_REPEATS to start fresh cycle
            if len(used_indices) >= MAX_REPEATS:
                self.question_usage[usage_key] = []
        
        # Select a random question from available ones to add variation
        if available_indices:
            selected_idx, selected_question = random.choice(available_indices)
            # Track usage
            self.question_usage[usage_key].append(selected_idx)
            return selected_question
        
        # Fallback: return first question if no exclusion, or second if first is excluded
        if exclude_question and level_questions[0] == exclude_question and len(level_questions) > 1:
            return level_questions[1]
        return level_questions[0]
    
    def generate_questions(self, detected_skills: List[Dict], resume_text: Optional[str] = None) -> List[Dict]:
        """Generate interview questions from detected skills using AI, with fallback to question bank."""
        ai_questions = []
        # Try AI-based generation first if Ollama is available and resume text is provided
        if self.use_ollama and resume_text:
            ai_questions = self.generate_questions_with_ollama(detected_skills, resume_text)
            if ai_questions and len(ai_questions) >= 5:
                return ai_questions[:5]
        
        # Use question bank (either as fallback or to backfill AI questions)
        questions = ai_questions.copy() if ai_questions else []
        question_bank_dict = {e["skill"]: e for e in self.question_bank}
        
        # Track which skills already have questions
        skills_with_questions = {q["skill"] for q in questions}
        
        # If we have AI questions but need more, backfill from question bank
        # Otherwise, generate all from question bank
        for skill in detected_skills:
            if len(questions) >= 5:
                break
                
            skill_key = skill["key"]
            level = skill["level"]
            
            # Skip if we already have a question for this skill
            if skill_key in skills_with_questions:
                continue
            
            if skill_key not in question_bank_dict:
                continue
            
            # Use rotation logic to get next question
            question_text = self._get_next_question_from_bank(skill_key, level)
            if question_text:
                questions.append({
                    "skill": skill_key,
                    "level": level,
                    "question": question_text
                })
                skills_with_questions.add(skill_key)
        
        # If we still have fewer than 3 questions, backfill with intermediate questions
        if len(questions) < 3:
            for skill in detected_skills:
                if len(questions) >= 3:
                    break
                skill_key = skill["key"]
                if skill_key not in question_bank_dict:
                    continue
                
                # Skip if we already have a question for this skill
                if skill_key in skills_with_questions:
                    continue
                
                # Use rotation logic to get next intermediate question
                question_text = self._get_next_question_from_bank(skill_key, "intermediate")
                if question_text:
                    questions.append({
                        "skill": skill_key,
                        "level": "intermediate",
                        "question": question_text
                    })
                    skills_with_questions.add(skill_key)
        
        return questions[:5]  # Ensure max 5 questions
    
    def get_fresh_question(self, skill_key: str, level: str, exclude_question: Optional[str] = None, resume_text: Optional[str] = None) -> Optional[Dict]:
        """Get a fresh question for a specific skill and level, optionally excluding a current question."""
        # Try AI generation first if resume text is available
        if self.use_ollama and resume_text:
            try:
                # Create a single skill dict for AI generation
                skill_dict = {
                    "key": skill_key,
                    "name": next((e["displayName"] for e in self.question_bank if e["skill"] == skill_key), skill_key),
                    "level": level,
                    "context": ""
                }
                ai_questions = self.generate_questions_with_ollama([skill_dict], resume_text)
                if ai_questions:
                    # Filter out excluded question if provided
                    for q in ai_questions:
                        if q.get("skill", "").lower() == skill_key.lower() and q.get("question") != exclude_question:
                            return q
            except Exception as e:
                print(f"AI question generation failed for refresh: {str(e)}, using question bank")
        
        # Fallback to question bank with rotation
        question_text = self._get_next_question_from_bank(skill_key, level, exclude_question)
        if question_text:
            return {
                "skill": skill_key,
                "level": level,
                "question": question_text
            }
        
        return None
    
    def analyze(self, pdf_content: bytes, job_role: Optional[str] = None) -> Dict:
        """Main analysis function."""
        # Extract text
        text = self.extract_text(pdf_content)
        
        if not text or len(text.strip()) < 10:
            return {
                "skills": [],
                "questions": []
            }
        
        # Detect skills
        detected_skills = self.detect_skills(text, job_role)
        
        # Generate questions (pass resume text for AI generation)
        questions = self.generate_questions(detected_skills, resume_text=text)
        
        # Format response
        skills_response = [
            {
                "name": s["name"],
                "key": s["key"],
                "level": s["level"]
            }
            for s in detected_skills
        ]
        
        return {
            "skills": skills_response,
            "questions": questions
        }

