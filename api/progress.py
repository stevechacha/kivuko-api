from api.grades import MISSION_STEPS, patriotism_grade


def mark_step_complete(participant, step_number: int) -> None:
    from api.models import MissionStepProgress

    MissionStepProgress.objects.get_or_create(
        participant=participant,
        step_number=step_number,
    )


def build_mission_progress(participant) -> dict:
    completed = set(
        participant.mission_steps.values_list("step_number", flat=True)
    )
    steps = []
    current = 1
    for step in MISSION_STEPS:
        num = step["number"]
        if num in completed:
            status = "completed"
        elif num == min(
            s["number"] for s in MISSION_STEPS if s["number"] not in completed
        ):
            status = "active"
            current = num
        else:
            status = "locked"
        steps.append({**step, "status": status})

    grade = patriotism_grade(participant.patriotism_points)
    return {
        "steps": steps,
        "current_step": current,
        "completed_count": len(completed),
        "total_steps": len(MISSION_STEPS),
        "grade": grade,
        "patriotism_points": participant.patriotism_points,
    }
