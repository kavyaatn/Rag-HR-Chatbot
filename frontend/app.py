import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="HR Resource Query Chatbot",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .employee-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .skill-tag {
        background-color: #e1f5fe;
        color: #0277bd;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.1rem;
        display: inline-block;
    }
    .availability-available {
        color: #4caf50;
        font-weight: bold;
    }
    .availability-busy {
        color: #ff9800;
        font-weight: bold;
    }
    .availability-on_leave {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_chat_query(query: str, max_results: int = 5):
    """Send chat query to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"query": query, "max_results": max_results},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def get_employees():
    """Get all employees from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/employees", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def get_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except:
        return {}

def display_employee_card(employee: Dict):
    """Display employee information in a card format"""
    availability_class = f"availability-{employee['availability'].replace(' ', '_')}"
    
    st.markdown(f"""
    <div class="employee-card">
        <h4>👤 {employee['name']}</h4>
        <p><strong>Experience:</strong> {employee['experience_years']} years</p>
        <p><strong>Department:</strong> {employee.get('department', 'N/A')}</p>
        <p><strong>Location:</strong> {employee.get('location', 'N/A')}</p>
        <p><strong>Availability:</strong> <span class="{availability_class}">{employee['availability'].replace('_', ' ').title()}</span></p>
        <p><strong>Skills:</strong></p>
        <div>
            {''.join([f'<span class="skill-tag">{skill}</span>' for skill in employee['skills']])}
        </div>
        <p><strong>Recent Projects:</strong></p>
        <ul>
            {''.join([f'<li>{project}</li>' for project in employee['projects'][:3]])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'api_healthy' not in st.session_state:
    st.session_state.api_healthy = check_api_health()

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">👥 HR Resource Query Chatbot</h1>', unsafe_allow_html=True)
    
    # API Status
    if not st.session_state.api_healthy:
        st.error("🚨 Backend API is not running! Please start the FastAPI server first.")
        st.code("cd backend && uvicorn main:app --reload")
        if st.button("🔄 Retry Connection"):
            st.session_state.api_healthy = check_api_health()
            st.rerun()
        return
    else:
        st.success("✅ Connected to HR Chatbot API")
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Settings")
        max_results = st.slider("Max Results", 1, 10, 5)
        
        st.header("📊 Quick Stats")
        stats = get_stats()
        if stats:
            st.metric("Total Employees", stats.get('total_employees', 0))
            st.metric("Available", stats.get('available_employees', 0))
            st.metric("Avg Experience", f"{stats.get('average_experience', 0)} years")
        
        st.header("💡 Sample Queries")
        sample_queries = [
            "Find Python developers with 3+ years experience",
            "Who has worked on healthcare projects?",
            "Suggest people for a React Native project",
            "Find developers who know both AWS and Docker",
            "I need someone experienced with machine learning for a healthcare project",
            "Who is available and has experience with microservices?",
            "Find UI/UX designers with healthcare experience"
        ]
        
        for query in sample_queries:
            if st.button(f"💬 {query}", key=f"sample_{hash(query)}"):
                st.session_state.current_query = query
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Query input
        query = st.text_input(
            "Ask me about finding employees:",
            placeholder="e.g., Find Python developers with 3+ years experience",
            key="query_input",
            value=st.session_state.get('current_query', '')
        )
        
        col_send, col_clear = st.columns([1, 1])
        with col_send:
            send_clicked = st.button("🚀 Send Query", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        # Process query
        if send_clicked and query:
            with st.spinner("🤔 Searching for the best candidates..."):
                response = send_chat_query(query, max_results)
                
                if 'error' not in response:
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'type': 'user',
                        'message': query,
                        'timestamp': time.time()
                    })
                    st.session_state.chat_history.append({
                        'type': 'bot',
                        'message': response['response'],
                        'employees': response['matched_employees'],
                        'confidence': response['confidence_score'],
                        'timestamp': time.time()
                    })
                    
                    # Clear the input
                    if 'current_query' in st.session_state:
                        del st.session_state.current_query
                    st.rerun()
                else:
                    st.error(f"Error: {response['error']}")
        
        # Display chat history
        if st.session_state.chat_history:
            st.header("💭 Conversation History")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                if chat['type'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>👤 You:</strong><br>
                        {chat['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🤖 HR Assistant:</strong><br>
                        {chat['message']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show confidence score
                    if 'confidence' in chat:
                        confidence_pct = chat['confidence'] * 100
                        st.progress(chat['confidence'], f"Confidence: {confidence_pct:.1f}%")
                    
                    # Show matched employees
                    if 'employees' in chat and chat['employees']:
                        with st.expander(f"👥 View {len(chat['employees'])} Matched Employees", expanded=False):
                            for emp in chat['employees']:
                                display_employee_card(emp)
    
    with col2:
        st.header("📈 Analytics Dashboard")
        
        # Get current stats
        stats = get_stats()
        employees = get_employees()
        
        if stats and employees:
            # Availability Distribution
            st.subheader("👥 Availability Status")
            availability_data = {}
            for emp in employees:
                status = emp['availability'].replace('_', ' ').title()
                availability_data[status] = availability_data.get(status, 0) + 1
            
            if availability_data:
                fig_availability = px.pie(
                    values=list(availability_data.values()),
                    names=list(availability_data.keys()),
                    title="Employee Availability Distribution"
                )
                fig_availability.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_availability, use_container_width=True)
            
            # Experience Distribution
            st.subheader("📊 Experience Levels")
            experience_ranges = {
                "0-2 years": 0,
                "3-5 years": 0,
                "6-8 years": 0,
                "9+ years": 0
            }
            
            for emp in employees:
                exp = emp['experience_years']
                if exp <= 2:
                    experience_ranges["0-2 years"] += 1
                elif exp <= 5:
                    experience_ranges["3-5 years"] += 1
                elif exp <= 8:
                    experience_ranges["6-8 years"] += 1
                else:
                    experience_ranges["9+ years"] += 1
            
            fig_exp = px.bar(
                x=list(experience_ranges.keys()),
                y=list(experience_ranges.values()),
                title="Experience Distribution",
                labels={'x': 'Experience Range', 'y': 'Number of Employees'}
            )
            st.plotly_chart(fig_exp, use_container_width=True)
            
            # Top Skills
            st.subheader("🔧 Most In-Demand Skills")
            if 'top_skills' in stats:
                top_skills_df = pd.DataFrame(
                    stats['top_skills'][:8], 
                    columns=['Skill', 'Count']
                )
                fig_skills = px.bar(
                    top_skills_df,
                    x='Count',
                    y='Skill',
                    orientation='h',
                    title="Top Skills in Organization"
                )
                fig_skills.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_skills, use_container_width=True)
            
            # Department Distribution
            st.subheader("🏢 Department Overview")
            if 'department_distribution' in stats:
                dept_data = stats['department_distribution']
                fig_dept = px.bar(
                    x=list(dept_data.values()),
                    y=list(dept_data.keys()),
                    orientation='h',
                    title="Employees by Department"
                )
                fig_dept.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_dept, use_container_width=True)
        
        # Employee Browser
        st.header("🔍 Employee Browser")
        if employees:
            # Filters
            with st.expander("🎛️ Filters", expanded=False):
                all_departments = list(set([emp.get('department', 'Unknown') for emp in employees if emp.get('department')]))
                all_skills = list(set([skill for emp in employees for skill in emp['skills']]))
                
                filter_dept = st.selectbox("Department", ["All"] + sorted(all_departments))
                filter_availability = st.selectbox("Availability", ["All", "available", "busy", "on_leave"])
                filter_min_exp = st.slider("Minimum Experience", 0, 10, 0)
                filter_skills = st.multiselect("Must have skills", sorted(all_skills))
            
            # Apply filters
            filtered_employees = employees.copy()
            
            if filter_dept != "All":
                filtered_employees = [emp for emp in filtered_employees if emp.get('department') == filter_dept]
            
            if filter_availability != "All":
                filtered_employees = [emp for emp in filtered_employees if emp['availability'] == filter_availability]
            
            if filter_min_exp > 0:
                filtered_employees = [emp for emp in filtered_employees if emp['experience_years'] >= filter_min_exp]
            
            if filter_skills:
                filtered_employees = [
                    emp for emp in filtered_employees 
                    if any(skill in emp['skills'] for skill in filter_skills)
                ]
            
            st.write(f"**Found {len(filtered_employees)} employees matching criteria:**")
            
            # Display filtered employees
            for emp in filtered_employees[:5]:  # Show first 5
                with st.expander(f"👤 {emp['name']} ({emp['experience_years']} years)", expanded=False):
                    display_employee_card(emp)
            
            if len(filtered_employees) > 5:
                st.info(f"+ {len(filtered_employees) - 5} more employees. Adjust filters to see more specific results.")

# Advanced Search Page
def advanced_search_page():
    st.header("🔍 Advanced Employee Search")
    
    with st.form("advanced_search"):
        col1, col2 = st.columns(2)
        
        with col1:
            skills_input = st.text_input("Skills (comma-separated)", placeholder="Python, React, AWS")
            min_exp = st.number_input("Minimum Experience (years)", min_value=0, max_value=20, value=0)
            department = st.text_input("Department", placeholder="Engineering, Data Science")
        
        with col2:
            max_exp = st.number_input("Maximum Experience (years)", min_value=0, max_value=20, value=20)
            availability = st.selectbox("Availability", ["All", "available", "busy", "on_leave"])
            max_results = st.number_input("Max Results", min_value=1, max_value=50, value=10)
        
        submitted = st.form_submit_button("🔍 Search Employees")
    
    if submitted:
        # Build search URL
        params = {}
        if skills_input:
            params['skills'] = skills_input
        if min_exp > 0:
            params['min_experience'] = min_exp
        if max_exp < 20:
            params['max_experience'] = max_exp
        if availability != "All":
            params['availability'] = availability
        if department:
            params['department'] = department
        if max_results:
            params['max_results'] = max_results
        
        # Make API call
        try:
            response = requests.get(f"{API_BASE_URL}/employees/search", params=params)
            if response.status_code == 200:
                results = response.json()
                
                st.success(f"✅ Found {len(results)} matching employees")
                
                if results:
                    # Display results
                    for emp in results:
                        display_employee_card(emp)
                else:
                    st.info("No employees found matching your criteria. Try adjusting the search parameters.")
            else:
                st.error(f"Search failed: {response.status_code}")
        except Exception as e:
            st.error(f"Error performing search: {str(e)}")

# System Status Page
def system_status_page():
    st.header("⚙️ System Status & Information")
    
    # API Health Check
    st.subheader("🔧 API Health")
    api_healthy = check_api_health()
    
    if api_healthy:
        st.success("✅ Backend API is running and healthy")
        
        # Get system info
        try:
            response = requests.get(f"{API_BASE_URL}/")
            if response.status_code == 200:
                info = response.json()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("API Status", info.get('status', 'Unknown'))
                with col2:
                    st.metric("Employees Loaded", info.get('employees_loaded', 0))
                with col3:
                    st.metric("API Version", "1.0.0")
        except:
            st.warning("Could not retrieve detailed API information")
    else:
        st.error("❌ Backend API is not accessible")
        st.info("Make sure to start the FastAPI server:")
        st.code("cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    # System Statistics
    st.subheader("📊 System Statistics")
    stats = get_stats()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Employees", stats.get('total_employees', 0))
        with col2:
            st.metric("Available Now", stats.get('available_employees', 0))
        with col3:
            st.metric("Average Experience", f"{stats.get('average_experience', 0)} years")
        with col4:
            departments = len(stats.get('department_distribution', {}))
            st.metric("Departments", departments)
        
        # Detailed breakdown
        st.subheader("📈 Detailed Analytics")
        
        if 'top_skills' in stats:
            st.write("**Top 10 Skills:**")
            skills_df = pd.DataFrame(stats['top_skills'], columns=['Skill', 'Count'])
            st.dataframe(skills_df.head(10), use_container_width=True)
        
        if 'department_distribution' in stats:
            st.write("**Department Distribution:**")
            dept_df = pd.DataFrame(
                list(stats['department_distribution'].items()),
                columns=['Department', 'Employee Count']
            )
            st.dataframe(dept_df, use_container_width=True)
    
    # Chat History Statistics
    if st.session_state.chat_history:
        st.subheader("💬 Chat Session Statistics")
        total_queries = len([chat for chat in st.session_state.chat_history if chat['type'] == 'user'])
        st.metric("Queries This Session", total_queries)
        
        # Average confidence
        confidences = [
            chat['confidence'] for chat in st.session_state.chat_history 
            if chat['type'] == 'bot' and 'confidence' in chat
        ]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            st.metric("Average Confidence", f"{avg_confidence * 100:.1f}%")

# Navigation
def main_navigation():
    st.sidebar.title("🧭 Navigation")
    
    pages = {
        "💬 Chat Interface": main,
        "🔍 Advanced Search": advanced_search_page,
        "⚙️ System Status": system_status_page
    }
    
    selected_page = st.sidebar.radio("Select Page", list(pages.keys()))
    
    # Page info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 About")
    st.sidebar.info(
        "This HR Resource Query Chatbot uses RAG (Retrieval-Augmented Generation) "
        "to help you find the right employees for your projects using natural language queries."
    )
    
    st.sidebar.markdown("### 🚀 Quick Start")
    st.sidebar.markdown("""
    1. **Chat Interface**: Ask natural language questions
    2. **Advanced Search**: Use structured filters
    3. **System Status**: View analytics and health
    """)
    
    return pages[selected_page]

# Run the app
if __name__ == "__main__":
    selected_page_func = main_navigation()
    selected_page_func()
