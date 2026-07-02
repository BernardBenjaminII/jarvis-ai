from knowledge_engine.queue.models import QueueItem
from knowledge_engine.queue.priorities import CATEGORY_PRIORITY


class ProcessingQueueBuilder:

    def build(self, documents):

        queue = []

        for doc in documents:

            priority = CATEGORY_PRIORITY.get(
                doc.category,
                25,
            )

            queue.append(
                QueueItem(
                    document_path=doc.path,
                    priority=priority,
                    reason=f"category={doc.category}",
                )
            )

        queue.sort(
            key=lambda q: q.priority,
            reverse=True,
        )

        return queue
