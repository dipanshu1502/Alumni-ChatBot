import unittest
from unittest.mock import patch

import rag_pipeline


class RAGPipelineTests(unittest.TestCase):
    def test_alumni_name_list_keeps_all_fetched_names_in_model_context(self):
        portal_items = [
            {
                "source": "alumni",
                "data": {"name": f"Alumni {index}"},
                "fetched_at": "2026-11-03T12:00:00",
            }
            for index in range(66)
        ]
        captured_prompt = {}

        def capture_prompt(prompt):
            captured_prompt["prompt"] = prompt
            return "Alumni list"

        with (
            patch.object(rag_pipeline, "fetch_relevant_portal_data", return_value=portal_items) as fetch,
            patch.object(rag_pipeline, "search_documents", return_value=[]),
            patch.object(rag_pipeline, "_answer_with_groq", side_effect=capture_prompt),
        ):
            result = rag_pipeline.generate_answer("show all alumni names")

        self.assertEqual(fetch.call_args.kwargs["limit_per_endpoint"], 100)
        self.assertEqual(captured_prompt["prompt"].count("Source: portal:alumni"), 66)
        self.assertIn("Alumni 65", captured_prompt["prompt"])
        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
