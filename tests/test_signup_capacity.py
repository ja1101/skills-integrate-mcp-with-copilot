import json
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient

import src.app as app_module


def test_signup_rejects_when_activity_is_full(tmp_path, monkeypatch):
    data_file = tmp_path / "activities.json"
    data = {
        "Full Club": {
            "description": "Already full activity",
            "schedule": "Fridays, 4:00 PM - 5:00 PM",
            "max_participants": 1,
            "participants": ["existing@mergington.edu"],
        }
    }
    data_file.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(app_module, "activities_file_path", Path(data_file))

    activity_name = "Full Club"
    encoded_activity_name = quote(activity_name, safe="")

    with TestClient(app_module.app) as client:
        response = client.post(
            f"/activities/{encoded_activity_name}/signup",
            params={"email": "newstudent@mergington.edu"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"

    persisted_data = json.loads(data_file.read_text(encoding="utf-8"))
    assert persisted_data[activity_name]["participants"] == ["existing@mergington.edu"]
