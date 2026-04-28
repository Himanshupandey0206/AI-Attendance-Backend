import google.generativeai as genai
from app.core.config import settings
from app.db.mongodb import get_database
from datetime import datetime
from bson.objectid import ObjectId

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

async def fetch_attendance_summary(date: str):
    db = get_database()
    cursor = db["attendance"].find({"date": date})
    records = await cursor.to_list(length=1000)
    
    total = len(records)
    present = sum(1 for r in records if r.get("status") == "Present")
    incomplete = sum(1 for r in records if r.get("status") == "Incomplete")
    
    return f"On {date}, total records: {total}. Present: {present}. Incomplete: {incomplete}."

async def fetch_latecomers(date: str):
    db = get_database()
    cursor = db["attendance"].find({"date": date})
    records = await cursor.to_list(length=1000)
    
    late_users = []
    for r in records:
        if "punch_in" in r and r["punch_in"]:
            # Assuming standard time is 09:00 AM
            punch_in_time = r["punch_in"]["time"]
            if punch_in_time.hour >= 9 and punch_in_time.minute > 0:
                user = await db["users"].find_one({"_id": ObjectId(r["user_id"])})
                if user:
                    late_users.append(f"{user['name']} (Punched in at {punch_in_time.strftime('%H:%M')})")
                    
    if not late_users:
        return f"No one was late on {date}."
    return f"Latecomers on {date}:\n" + "\n".join(late_users)

async def process_ai_query(query: str, role: str) -> str:
    """Processes natural language query using Gemini API and context from DB."""
    if not settings.GEMINI_API_KEY:
        return "Gemini API key is not configured on the server."
        
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Simple rule-based extraction for demonstration; 
    # In a fully productionized system, we would use Gemini Function Calling (Tools) to decide which func to call.
    context = ""
    
    query_lower = query.lower()
    if "late" in query_lower:
        context = await fetch_latecomers(today)
    elif "summary" in query_lower or "how many" in query_lower:
        context = await fetch_attendance_summary(today)
    elif "who" in query_lower or "joined" in query_lower or "present" in query_lower:
        db = get_database()
        cursor = db["attendance"].find({"date": today})
        records = await cursor.to_list(length=1000)
        present_users = []
        for r in records:
            if "punch_in" in r and r["punch_in"]:
                user = await db["users"].find_one({"_id": ObjectId(r["user_id"])})
                if user:
                    present_users.append(user["name"])
        if present_users:
            context = f"People who have punched in today: {', '.join(present_users)}."
        else:
            context = "No one has punched in today."
    elif "overtime" in query_lower:
        db = get_database()
        cursor = db["overtime_requests"].find({"status": "Pending"})
        records = await cursor.to_list(length=100)
        context = f"There are {len(records)} pending overtime requests."
    elif "less than 8" in query_lower or "8 hours" in query_lower:
        db = get_database()
        cursor = db["attendance"].find({"date": today})
        records = await cursor.to_list(length=1000)
        under_8_users = []
        for r in records:
            if "total_hours" in r and r["total_hours"] is not None and r["total_hours"] < 8:
                user = await db["users"].find_one({"_id": ObjectId(r["user_id"])})
                if user:
                    under_8_users.append(f"{user['name']} ({r['total_hours']:.1f} hrs)")
        if under_8_users:
            context = f"Employees with less than 8 hours today: {', '.join(under_8_users)}."
        else:
            context = "No employees have less than 8 hours today, or they haven't punched out yet."
    else:
        context = "The system can answer queries about today's attendance summary, latecomers, and pending overtime requests."

    prompt = f"""
    You are an AI assistant for an Attendance Management System.
    The user (Role: {role}) asked: "{query}"
    
    Here is the data context fetched from the database:
    {context}
    
    Answer the user's question concisely and conversationally based ONLY on the provided data context.
    Note: "joining", "punching in", and "being present" all mean the exact same thing in this context. 
    If the context doesn't contain the answer, say you don't have that information.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"
