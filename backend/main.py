from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import os
from pathlib import Path

from models import Employee, ChatQuery, ChatResponse, SearchFilters, AvailabilityStatus
from rag_system import RAGSystem

# Initialize FastAPI app
app = FastAPI(
    title="HR Resource Query Chatbot API",
    description="AI-powered HR assistant for finding employees based on natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load employee data
def load_employee_data():
    """Load employee data from JSON file or use sample data"""
    data_file = Path(__file__).parent / "data" / "employees.json"
    
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        # Use sample data from the import
        from backend.rag_system import SAMPLE_EMPLOYEES
        return SAMPLE_EMPLOYEES

# Initialize RAG system
try:
    employee_data = load_employee_data()
    rag_system = RAGSystem(employee_data)
    print(f"✅ RAG System initialized with {len(employee_data)} employees")
except Exception as e:
    print(f"❌ Error initializing RAG system: {e}")
    rag_system = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "HR Resource Query Chatbot API is running!",
        "status": "healthy",
        "employees_loaded": len(rag_system.employees) if rag_system else 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_query(query: ChatQuery):
    """
    Process natural language query and return matching employees with AI-generated response
    """
    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    try:
        response = rag_system.generate_response(query.query, query.max_results)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/employees", response_model=List[Employee])
async def get_all_employees():
    """Get all employees"""
    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    return rag_system.employees

@app.get("/employees/search", response_model=List[Employee])
async def search_employees(
    skills: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    availability: Optional[AvailabilityStatus] = None,
    department: Optional[str] = None,
    max_results: Optional[int] = 10
):
    """
    Search employees with structured filters
    """
    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    filtered_employees = []
    skills_list = [s.strip() for s in skills.split(',')] if skills else []
    
    for emp in rag_system.employees:
        # Filter by skills
        if skills_list:
            emp_skills_lower = [s.lower() for s in emp.skills]
            if not any(skill.lower() in emp_skills_lower for skill in skills_list):
                continue
        
        # Filter by experience
        if min_experience and emp.experience_years < min_experience:
            continue
        if max_experience and emp.experience_years > max_experience:
            continue
        
        # Filter by availability
        if availability and emp.availability != availability:
            continue
        
        # Filter by department
        if department and emp.department and department.lower() not in emp.department.lower():
            continue
        
        filtered_employees.append(emp)
    
    return filtered_employees[:max_results] if max_results else filtered_employees

@app.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: int):
    """Get specific employee by ID"""
    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    employee = next((emp for emp in rag_system.employees if emp.id == employee_id), None)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    employees = rag_system.employees
    
    # Calculate statistics
    total_employees = len(employees)
    available_employees = len([e for e in employees if e.availability == "available"])
    avg_experience = sum(e.experience_years for e in employees) / total_employees
    
    # Skills distribution
    all_skills = []
    for emp in employees:
        all_skills.extend(emp.skills)
    
    skill_counts = {}
    for skill in all_skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Department distribution
    dept_counts = {}
    for emp in employees:
        if emp.department:
            dept_counts[emp.department] = dept_counts.get(emp.department, 0) + 1
    
    return {
        "total_employees": total_employees,
        "available_employees": available_employees,
        "average_experience": round(avg_experience, 1),
        "top_skills": top_skills,
        "department_distribution": dept_counts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)