from knowledge_engine.receiving.report import print_report
from knowledge_engine.receiving.scanner import scan


class ReceivingDepartment:

    def receive(self, root: str):

        accepted, rejected = scan(root)

        print_report(accepted, rejected)

        return accepted
