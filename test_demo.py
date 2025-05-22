import redis
import time
from datetime import datetime, timedelta
from domain.models.task import Task
from domain.models.talent import Talent
from domain.services.extension import ExtensionService
from domain.services.matching import MatchingService

def print_header(title):
    print("\n" + "="*len(title))
    print(title)
    print("="*len(title))

def test_demo_end_to_end():
    redis_client = redis.Redis(host="localhost", port=6379, db=0)

    # Clean up any previous test data
    redis_client.delete("task:task_001")
    redis_client.delete("talent:talent_001")
    redis_client.delete("talent:talent_002")
    redis_client.delete("talent:talent_003")

    # 1. Create and save a talent
    print_header("Step 1: Create and Save Talents")
    talent1 = Talent(
        talent_id="talent_001",
        name="Alice",
        skills=["python", "django"],
        available=True,
        rating=4.7
    )
    talent2 = Talent(
        talent_id="talent_002",
        name="Bob",
        skills=["python", "flask"],
        available=True,
        rating=4.5
    )
    talent1.to_redis(redis_client)
    talent2.to_redis(redis_client)
    print(f"Saved talents: {talent1.talent_id}, {talent2.talent_id}")

    # 2. Create and save a task
    print_header("Step 2: Create and Save Task")
    task = Task(
        task_id="task_001",
        assigned_to=None,
        claimed_at=None,
        deadline=(datetime.utcnow() + timedelta(seconds=2)).isoformat(),
        status="unassigned",
        extensions=[],
        matches={"talent_001": 0.9, "talent_002": 0.8}
    )
    task.to_redis(redis_client)
    print(f"Task created and saved: {task.task_id}")

    # 3. Load the task and a talent
    print_header("Step 3: Load Task and Talent")
    loaded_task = Task.from_redis(redis_client, "task_001")
    loaded_talent = Talent.from_redis(redis_client, "talent_001")
    print(f"Loaded task: {loaded_task}")
    print(f"Loaded talent: {loaded_talent}")

    # 4. Assign the task to the best-suited talent
    print_header("Step 4: Assign Task to Best Talent")
    best_talent = MatchingService.get_best_match(loaded_task)
    if best_talent:
        loaded_task.assigned_to = best_talent
        loaded_task.status = "assigned"
        loaded_task.to_redis(redis_client)
        redis_client.hset(f"talent:{best_talent}", "available", "false")
        print(f"Task {loaded_task.task_id} assigned to talent {best_talent}")
    else:
        print("No suitable talent found.")

    # 5. Wait for task to become overdue
    print_header("Step 5: Wait for Task to Become Overdue")
    print("Waiting for task deadline to pass...")
    time.sleep(3)

        # 6. Monitor the task for overdue status
    print_header("Step 6: Monitor Task for Overdue Status")
    is_overdue = loaded_task.is_overdue()
    print(f"Is task overdue? {'Yes' if is_overdue else 'No'}")

    # 7. Evaluate an extension request using Gemini AI (simulate a request)
    print_header("Step 7: Evaluate Extension Request Using Gemini AI")
    extension_requested = not loaded_task.has_requested_extension()
    extension_approved = False
    if extension_requested:
        reason = "Need more time."
        extension_approved = ExtensionService.evaluate_request(loaded_task, reason)
        print(f"Extension request for task {loaded_task.task_id} {'approved' if extension_approved else 'rejected'}.")
        if extension_approved:
            loaded_task.extensions.append({"reason": reason, "approved": True})
            loaded_task.to_redis(redis_client)
    else:
        print("No extension requested.")

    # 8. Reassign if overdue and (no extension or extension rejected)
    print_header("Step 8: Reassign Task if Needed")
    if is_overdue and (not extension_requested or not extension_approved):
        next_talent = MatchingService.get_next_available(loaded_task.task_id)
        if next_talent:
            loaded_task.assigned_to = next_talent
            loaded_task.status = "reassigned"
            loaded_task.to_redis(redis_client)
            print(f"Task {loaded_task.task_id} reassigned to talent {next_talent}")
        else:
            print("No available talent to reassign task.")
    else:
        print("No reassignment needed.")


if __name__ == "__main__":
    test_demo_end_to_end()