import redis
from domain.models.task import Task
from domain.models.talent import Talent
from domain.services.extension import ExtensionService
from domain.utils.logging import logger


def main():
    """
    Main entry point for the Talent Match application.
    This function demonstrates the core functionalities of the application.
    """
    # Initialize Redis client
    redis_client = redis.Redis(host="localhost", port=6379, db=0)

    # Create and save a task to Redis
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

    # Load a task from Redis
    logger.info("Loading a task from Redis...")
    loaded_task = Task.from_redis(redis_client, "task_001")
    if loaded_task:
        logger.info(f"Loaded task: {loaded_task}")

    # Evaluate an extension request
    logger.info("Evaluating an extension request...")
    reason = "Need more time to complete the task due to unforeseen circumstances."
    if loaded_task:
        decision = ExtensionService.evaluate_request(loaded_task, reason)
        logger.info(f"Extension request decision for task {loaded_task.task_id}: {'APPROVED' if decision else 'REJECTED'}")

    # Create and save a talent to Redis
    logger.info("Creating and saving a talent to Redis...")
    talent = Talent(
        talent_id="talent_001",
        available=True,
        rating=4.5
    )
    if talent.to_redis(redis_client):
        logger.info(f"Talent {talent.talent_id} saved successfully.")

    # Load a talent from Redis
    logger.info("Loading a talent from Redis...")
    loaded_talent = Talent.from_redis(redis_client, "talent_001")
    if loaded_talent:
        logger.info(f"Loaded talent: {loaded_talent}")

    # Bulk save talents
    logger.info("Bulk saving talents to Redis...")
    talents = [
        Talent(talent_id="talent_002", available=True, rating=4.8),
        Talent(talent_id="talent_003", available=False, rating=3.9),
    ]
    saved_count = Talent.bulk_save(redis_client, talents)
    logger.info(f"Successfully saved {saved_count} talents in bulk.")

    # Check if a task is overdue
    logger.info("Checking if a task is overdue...")
    if loaded_task and loaded_task.is_overdue():
        logger.info(f"Task {loaded_task.task_id} is overdue.")
    else:
        logger.info(f"Task {loaded_task.task_id} is not overdue.")

    # Add an extension to a task
    logger.info("Adding an extension to a task...")
    if loaded_task:
        loaded_task.add_extension("Need more time due to technical issues.")
        logger.info(f"Extensions for task {loaded_task.task_id}: {loaded_task.extensions}")


if __name__ == "__main__":
    main()