"""Check the adapter's contract with the real benchmark, without API calls."""
import unittest

from benchmark import RetailBenchmark


class BenchmarkTests(unittest.TestCase):
    def test_official_tool_schemas_are_preserved(self):
        bench = RetailBenchmark("0", lambda *_: None)
        for official, wrapped in zip(bench.environment.get_tools(), bench.tools(), strict=True):
            self.assertEqual(wrapped.info.raw_schema, official.openai_schema["function"])

    def test_mutation_changes_only_this_runs_database(self):
        events = []
        bench = RetailBenchmark("0", lambda kind, data: events.append((kind, data)))
        before = bench.environment.get_db_hash()
        # Replay the official reference actions only in this adapter test, never in the agent.
        for action in bench.task.evaluation_criteria.actions:
            result = bench.execute(action.name, action.arguments, action.action_id)
            self.assertFalse(result.error, result.content)
        self.assertNotEqual(before, bench.environment.get_db_hash())
        self.assertEqual(bench.snapshot()["orders"]["#W2378156"]["status"], "exchange requested")
        fresh = RetailBenchmark("0", lambda *_: None)
        self.assertEqual(before, fresh.environment.get_db_hash())
        self.assertEqual(events[-1][0], "tool_finished")

    def test_invalid_tool_arguments_are_reported_as_errors(self):
        bench = RetailBenchmark("0", lambda *_: None)
        result = bench.execute("get_order_details", {"order_id": "does-not-exist"}, "bad-order")
        self.assertTrue(result.error)


if __name__ == "__main__":
    unittest.main()
