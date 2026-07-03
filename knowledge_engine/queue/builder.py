from knowledge_engine.queue.models import QueueItem
from knowledge_engine.queue.priorities import CATEGORY_PRIORITY


class ProcessingQueueBuilder:
    """
    Builds processing queues.

    Supports both the legacy document pipeline and the
    Knowledge Object pipeline.
    """

    #
    # ------------------------------------------------------------------
    # Legacy
    # ------------------------------------------------------------------
    #

    def build_from_documents(self, documents):

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

        return self.sort(queue)

    #
    # ------------------------------------------------------------------
    # Knowledge Objects
    # ------------------------------------------------------------------
    #

    def build_from_registry(self, registry_objects):

        queue = []

        for obj in registry_objects:

            priority = self.priority_for_object(obj)

            queue.append(
                QueueItem(
                    object_uuid=obj["object_uuid"],
                    object_path=obj["object_path"],
                    object_type=obj["object_type"],
                    priority=priority,
                    lifecycle_state=obj["lifecycle_state"],
                    reason=f"registry:{obj['object_type']}",
                )
            )

        return self.sort(queue)

    #
    # ------------------------------------------------------------------
    # Priority
    # ------------------------------------------------------------------
    #

    def priority_for_object(self, obj):

        object_type = obj["object_type"]

        if object_type == "website_archive":
            return 90

        if object_type == "academic_or_code_project":
            return 85

        if object_type == "single_document":
            return 80

        if object_type == "web_or_html_collection":
            return 70

        if object_type == "folder_collection":
            return 60

        if object_type == "single_file":
            return 40

        return 50

    #
    # ------------------------------------------------------------------
    # Shared
    # ------------------------------------------------------------------
    #

    def sort(self, queue):

        queue.sort(
            key=lambda item: item.priority,
            reverse=True,
        )

        return queue
