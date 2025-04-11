from config.redis import get_redis
from domain.models import Task, Talent

class MatchingService:
    @staticmethod
    def get_next_available(task_id: str) -> str | None:
        """Get next best available talent"""
        redis = get_redis()
        
        # Load the task
        task = Task.from_redis(redis, task_id)
        if not task or not task.matches:
            return None
            
        # Check talents in score order
        for talent_id, score in sorted(task.matches.items(), 
                                     key=lambda x: -x[1]):  # Descending
            
            talent = Talent.from_redis(redis, talent_id)
            if talent and talent.available:
                return talent_id
                
        return None