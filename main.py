import redis
from domain.models.task import Task
from domain.models.talent import Talent
from domain.services.extension import ExtensionService
from domain.services.matching import MatchingService
from domain.utils.logging import logger


def create_and_save_task(redis_client):
    """Create and save a task to Redis."""
    logger.info("Creating and saving a task to Redis...")
    task = Task(
        task_id="task_001",
        assigned_to="talent_001",
        claimed_at=None,
        deadline=None,
        status="unassigned",
        extensions=[],
        matches={"talent_001": 0.9, "talent_002": 0.8}
    )
    if task.to_redis(redis_client):
        logger.info(f"Task {task.task_id} saved successfully.")
    return task


def load_task_and_talent(redis_client, task_id, talent_id):
    """Load a task and a talent from Redis."""
    logger.info("Loading a task from Redis...")
    task = Task.from_redis(redis_client, task_id)
    if task:
        logger.info(f"Loaded task: {task}")

    logger.info("Loading a talent from Redis...")
    talent = Talent.from_redis(redis_client, talent_id)
    if talent:
        logger.info(f"Loaded talent: {talent}")

    return task, talent


def assign_task_to_best_talent(task, redis_client):
    """Assign the task to the best-suited talent."""
    logger.info("Assigning task to the best-suited talent...")
    best_talent = MatchingService.get_best_match(task)
    if best_talent:
        task.assigned_to = best_talent
        task.to_redis(redis_client)
        logger.info(f"Task {task.task_id} assigned to talent {best_talent}.")
    else:
        logger.warning(f"No suitable talent found for task {task.task_id}.")


def monitor_task(task):
    """Monitor the task for overdue status."""
    logger.info("Monitoring task...")
    if task.is_overdue():
        logger.info(f"Task {task.task_id} is overdue.")
        return True
    else:
        logger.info(f"Task {task.task_id} is not overdue.")
        return False


def reassign_task_if_needed(task, redis_client):
    """Reassign the task if no extension is requested after the deadline."""
    logger.info("Checking if reassignment is needed...")
    if task.is_overdue() and not task.has_requested_extension():
        logger.info(f"Reassigning task {task.task_id} to the next best talent...")
        best_talent = MatchingService.get_next_available(task.task_id)
        if best_talent:
            task.assigned_to = best_talent
            task.to_redis(redis_client)
            logger.info(f"Task {task.task_id} reassigned to talent {best_talent}.")
        else:
            logger.warning(f"No available talent to reassign task {task.task_id}.")


def evaluate_extension_request(task):
    """Evaluate an extension request using Gemini AI."""
    logger.info("Evaluating an extension request...")
    reason = "Need more time to complete the task due to unforeseen circumstances."
    decision = ExtensionService.evaluate_request(task, reason)
    if decision:
        logger.info(f"Extension request for task {task.task_id} approved.")
    else:
        logger.info(f"Extension request for task {task.task_id} rejected.")


def main():
    """
    Main entry point for the Talent Match application.
    This function demonstrates the core functionalities of the application.
    """

    redis_client = redis.Redis(host="localhost", port=6379, db=0)

    task = create_and_save_task(redis_client)

    loaded_task, loaded_talent = load_task_and_talent(redis_client, "task_001", "talent_001")

    if loaded_task:
        assign_task_to_best_talent(loaded_task, redis_client)

    if loaded_task:
        is_overdue = monitor_task(loaded_task)

    if loaded_task and is_overdue:
        reassign_task_if_needed(loaded_task, redis_client)

    if loaded_task:
        evaluate_extension_request(loaded_task)


if __name__ == "__main__":
    main()