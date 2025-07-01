import json
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from models import Employee, ChatResponse
import os
from dotenv import load_dotenv

load_dotenv()

class RAGSystem:
    def __init__(self, employees_data: List[Dict]):
        self.employees = [Employee(**emp) for emp in employees_data]
        self.employee_embeddings = None
        self.employee_texts = None
        self.vectorizer = None
        self._initialize_embeddings()
        
    def _initialize_embeddings(self):
        """Initialize embeddings with fallback options"""
        try:
            # Try to use sentence-transformers first
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_sentence_transformers = True
            self._build_sentence_embeddings()
            print("✅ Using Sentence Transformers for embeddings")
        except ImportError as e:
            print(f"⚠️ Sentence Transformers not available: {e}")
            print("📋 Falling back to TF-IDF embeddings")
            self.use_sentence_transformers = False
            self._build_tfidf_embeddings()
    
    def _build_sentence_embeddings(self):
        """Build embeddings using sentence transformers"""
        self.employee_texts = []
        for emp in self.employees:
            text = f"""
            Name: {emp.name}
            Skills: {', '.join(emp.skills)}
            Experience: {emp.experience_years} years
            Projects: {', '.join(emp.projects)}
            Department: {emp.department}
            Specializations: {', '.join(emp.specializations or [])}
            Availability: {emp.availability}
            Location: {emp.location}
            """
            self.employee_texts.append(text.strip())
        
        self.employee_embeddings = self.model.encode(self.employee_texts)
    
    def _build_tfidf_embeddings(self):
        """Build embeddings using TF-IDF as fallback"""
        self.employee_texts = []
        for emp in self.employees:
            # Create searchable text
            text_parts = []
            text_parts.extend(emp.skills)
            text_parts.extend(emp.projects)
            text_parts.append(emp.name)
            text_parts.append(emp.department or "")
            text_parts.extend(emp.specializations or [])
            text_parts.append(emp.availability)
            text_parts.append(emp.location or "")
            text_parts.append(f"{emp.experience_years} years experience")
            
            # Join all text parts
            text = " ".join(text_parts).lower()
            self.employee_texts.append(text)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Fit and transform
        self.employee_embeddings = self.vectorizer.fit_transform(self.employee_texts)
    
    def _extract_requirements(self, query: str) -> Dict:
        """Extract requirements from natural language query"""
        requirements = {
            'skills': [],
            'experience': None,
            'projects': [],
            'availability': None,
            'department': None
        }
        
        # Extract experience requirements
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(experience|exp)',
            r'with\s*(\d+)\+?\s*years?',
            r'(\d+)\s*years?\s*of\s*experience'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, query.lower())
            if match:
                requirements['experience'] = int(match.group(1))
                break
        
        # Extract availability
        if 'available' in query.lower():
            requirements['availability'] = 'available'
        
        # Extract common skills mentioned
        common_skills = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue',
            'node', 'express', 'django', 'flask', 'fastapi',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'machine learning', 'ml', 'ai', 'data science',
            'sql', 'postgresql', 'mongodb', 'redis',
            'html', 'css', 'typescript', 'go', 'rust',
            'tensorflow', 'pytorch', 'scikit-learn'
        ]
        
        query_lower = query.lower()
        for skill in common_skills:
            if skill in query_lower:
                requirements['skills'].append(skill)
        
        return requirements
    
    def search_employees(self, query: str, max_results: int = 5) -> Tuple[List[Employee], List[float]]:
        """Search employees using available embedding method"""
        if self.use_sentence_transformers:
            return self._search_with_sentence_transformers(query, max_results)
        else:
            return self._search_with_tfidf(query, max_results)
    
    def _search_with_sentence_transformers(self, query: str, max_results: int) -> Tuple[List[Employee], List[float]]:
        """Search using sentence transformers"""
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.employee_embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:max_results * 2]  # Get more to filter
        
        # Apply requirements filtering
        requirements = self._extract_requirements(query)
        filtered_results = []
        filtered_scores = []
        
        for idx in top_indices:
            emp = self.employees[idx]
            score = similarities[idx]
            
            if self._matches_requirements(emp, requirements):
                filtered_results.append(emp)
                filtered_scores.append(score)
                
                if len(filtered_results) >= max_results:
                    break
        
        return filtered_results, filtered_scores
    
    def _search_with_tfidf(self, query: str, max_results: int) -> Tuple[List[Employee], List[float]]:
        """Search using TF-IDF"""
        query_vector = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vector, self.employee_embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:max_results * 2]
        
        # Apply requirements filtering
        requirements = self._extract_requirements(query)
        filtered_results = []
        filtered_scores = []
        
        for idx in top_indices:
            emp = self.employees[idx]
            score = similarities[idx]
            
            if self._matches_requirements(emp, requirements):
                filtered_results.append(emp)
                filtered_scores.append(score)
                
                if len(filtered_results) >= max_results:
                    break
        
        # If no results with requirements, return top similarity matches
        if not filtered_results:
            for idx in top_indices[:max_results]:
                emp = self.employees[idx]
                score = similarities[idx]
                filtered_results.append(emp)
                filtered_scores.append(score)
        
        return filtered_results, filtered_scores
    
    def _matches_requirements(self, employee: Employee, requirements: Dict) -> bool:
        """Check if employee matches extracted requirements"""
        # Check experience
        if requirements['experience'] and employee.experience_years < requirements['experience']:
            return False
        
        # Check availability
        if requirements['availability'] and employee.availability != requirements['availability']:
            return False
        
        # Check skills (if any were extracted)
        if requirements['skills']:
            emp_skills_lower = [skill.lower() for skill in employee.skills]
            emp_text_lower = f"{' '.join(employee.skills)} {' '.join(employee.projects)} {employee.name}".lower()
            
            # Check if any required skill matches
            skill_match = False
            for req_skill in requirements['skills']:
                if (req_skill in emp_skills_lower or 
                    req_skill in emp_text_lower or
                    any(req_skill in skill.lower() for skill in employee.skills)):
                    skill_match = True
                    break
            
            if not skill_match:
                return False
        
        return True
    
    def generate_response(self, query: str, max_results: int = 5) -> ChatResponse:
        """Generate RAG response"""
        employees, scores = self.search_employees(query, max_results)
        
        if not employees:
            return ChatResponse(
                response="I couldn't find any employees matching your specific requirements. Please try rephrasing your query or adjusting the criteria.",
                matched_employees=[],
                confidence_score=0.0
            )
        
        # Generate natural language response
        response = self._format_response(query, employees, scores)
        avg_confidence = sum(scores) / len(scores) if scores else 0.0
        
        return ChatResponse(
            response=response,
            matched_employees=employees,
            confidence_score=avg_confidence
        )
    
    def _format_response(self, query: str, employees: List[Employee], scores: List[float]) -> str:
        """Format natural language response"""
        if len(employees) == 1:
            emp = employees[0]
            response = f"I found an excellent candidate for your requirements:\n\n"
            response += f"**{emp.name}** would be perfect for this role. "
            response += f"With {emp.experience_years} years of experience, they have worked on projects like "
            response += f"{', '.join(emp.projects[:2])}. "
            response += f"Their key skills include {', '.join(emp.skills[:5])}. "
            response += f"They are currently {emp.availability} and based in {emp.location}."
            
            if emp.specializations:
                response += f"\n\nTheir specializations include: {', '.join(emp.specializations)}."
        
        else:
            response = f"Based on your requirements, I found {len(employees)} excellent candidates:\n\n"
            
            for i, emp in enumerate(employees[:3], 1):  # Show top 3 detailed
                response += f"**{i}. {emp.name}** ({emp.experience_years} years experience)\n"
                response += f"   • Skills: {', '.join(emp.skills[:4])}\n"
                response += f"   • Recent projects: {', '.join(emp.projects[:2])}\n"
                response += f"   • Status: {emp.availability} | Location: {emp.location}\n"
                if emp.specializations:
                    response += f"   • Specializations: {', '.join(emp.specializations[:3])}\n"
                response += "\n"
            
            if len(employees) > 3:
                response += f"And {len(employees) - 3} more candidates available. "
        
        response += "\n\nWould you like me to provide more details about any of these candidates or help you with additional search criteria?"
        
        return response