"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import json
from pathlib import Path
from threading import Lock


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_activities_file()
    yield
    pass  # No cleanup needed on shutdown

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities",
              lifespan=lifespan)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
activity_file_lock = Lock()
activities_file_path = current_dir / "data" / "activities.json"

# Default data used to initialize the activity file if it does not exist yet.
DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    },
    "GitHub Skills": {
        "description": "Learn practical coding and collaboration skills using GitHub, part of the school's GitHub Certifications program",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 25,
        "participants": []
    }
}


def ensure_activities_file() -> None:
    """Create the activity data file with default content on first run."""
    activities_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not activities_file_path.exists():
        with activities_file_path.open("w", encoding="utf-8") as data_file:
            json.dump(DEFAULT_ACTIVITIES, data_file, indent=2)


def load_activities() -> dict:
    """Load all activities from the JSON data file."""
    ensure_activities_file()
    try:
        with activities_file_path.open("r", encoding="utf-8") as data_file:
            return json.load(data_file)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Activity data file is corrupted"
        ) from exc


def save_activities(activities: dict) -> None:
    """Persist all activities to the JSON data file."""
    with activities_file_path.open("w", encoding="utf-8") as data_file:
        json.dump(activities, data_file, indent=2)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return load_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with activity_file_lock:
        activities = load_activities()

        # Validate activity exists
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get the specific activity
        activity = activities[activity_name]

        # Validate student is not already signed up
        if email in activity["participants"]:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

        # Validate activity has available spots
        if len(activity["participants"]) >= activity["max_participants"]:
            raise HTTPException(
                status_code=400,
                detail="Activity is full"
            )

        # Add student and persist
        activity["participants"].append(email)
        save_activities(activities)

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with activity_file_lock:
        activities = load_activities()

        # Validate activity exists
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get the specific activity
        activity = activities[activity_name]

        # Validate student is signed up
        if email not in activity["participants"]:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        # Remove student and persist
        activity["participants"].remove(email)
        save_activities(activities)

    return {"message": f"Unregistered {email} from {activity_name}"}
