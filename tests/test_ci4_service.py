import unittest
from unittest.mock import patch

import ci4_service


class CI4ServiceTests(unittest.TestCase):
    def test_specific_question_routes_to_matching_public_endpoint(self):
        self.assertEqual(ci4_service.classify_question("Show me upcoming events"), ["events"])
        self.assertEqual(ci4_service.classify_question("Tell me about latest news"), ["news"])

    def test_unmatched_question_searches_all_chatbot_public_sources(self):
        self.assertEqual(
            ci4_service.classify_question("What is available on the website?"),
            list(ci4_service.PUBLIC_ENDPOINTS),
        )
        self.assertFalse(ci4_service.is_broad_portal_question("What is the opposite of this?"))

    def test_event_list_without_date_filter_returns_all_api_events(self):
        with patch.object(
            ci4_service,
            "fetch_public_endpoint",
            return_value=([], None, "2026-11-03T12:00:00"),
        ) as fetch:
            ci4_service.fetch_relevant_portal_data("show all events", targets=["events"])

        fetch.assert_called_once_with("events", {})

    def test_alumni_mentor_query_uses_the_public_directory_filter(self):
        with patch.object(
            ci4_service,
            "fetch_public_endpoint",
            return_value=([], None, "2026-11-03T12:00:00"),
        ) as fetch:
            ci4_service.fetch_relevant_portal_data("list alumni mentors")

        fetch.assert_called_once_with("alumni", {"mentor": "true"})

    def test_record_search_matches_allowlisted_field_names_and_hindi_values(self):
        records = [
            {"title": "Public job", "location": "Delhi"},
            {"title": "Another public job", "location": "Amritsar"},
        ]
        result = ci4_service._rank_records("which job has a location in Delhi", records, 1, "jobs")
        self.assertEqual(result, [records[0]])

        alumni = [
            {"name": "Akal Alumni", "city": "अमृतसर"},
            {"name": "Other Alumni", "city": "दिल्ली"},
        ]
        result = ci4_service._rank_records("अमृतसर के alumni", alumni, 5, "alumni")
        self.assertEqual(result, [alumni[0]])

    def test_alumni_mapping_drops_private_fields(self):
        record = ci4_service._map_record("alumni", {
            "first_name": "Akal",
            "last_name": "Alumni",
            "department": "Computer Science",
            "email": "private@example.test",
            "phone": "1234567890",
            "user_id": 42,
        })

        self.assertEqual(record["name"], "Akal Alumni")
        self.assertNotIn("email", record)
        self.assertNotIn("phone", record)
        self.assertNotIn("user_id", record)

    def test_name_list_returns_all_matching_names_up_to_limit(self):
        records = [{"name": f"Alumni {index}", "department": "CS"} for index in range(70)]
        with patch.object(
            ci4_service,
            "fetch_public_endpoint",
            return_value=(records, None, "2026-11-03T12:00:00"),
        ):
            result = ci4_service.fetch_relevant_portal_data(
                "show all alumni names",
                targets=["alumni"],
            )

        self.assertEqual(len(result), 70)
        self.assertEqual(result[0]["data"], {"name": "Alumni 0"})
        self.assertEqual(result[-1]["data"], {"name": "Alumni 69"})

    def test_broad_site_question_reads_every_allowlisted_public_endpoint(self):
        payloads = {
            "events": {"data": [{"title": "Public event", "created_by": 8, "virtual_link": "secret"}]},
            "alumni": {"data": [{"first_name": "Akal", "last_name": "Alumni", "phone": "secret"}]},
            "jobs": {"data": [{"title": "Public job", "contact_email": "secret@example.test"}]},
            "chapters": {"data": [{"name": "Public chapter", "lead_user_id": 8}]},
            "stories": {"data": [{"title": "Public story", "alumni_user_id": 8}]},
            "news": {"data": [{"title": "Public news", "created_by": 8}]},
            "gallery": {"data": [{"title": "Public album", "speaker_uid": "secret"}]},
            "donations": {"data": [{"title": "Public campaign", "created_by": 8}]},
            "stats": {"data": {"counts": {"total_alumni": 12, "total_students": 90}}},
        }
        ci4_service.clear_cache()
        with patch.object(ci4_service, "_get_json", side_effect=lambda endpoint, params: payloads[endpoint]):
            result = ci4_service.fetch_relevant_portal_data("What is available on the website?")
        ci4_service.clear_cache()

        self.assertEqual({item["source"] for item in result}, set(ci4_service.PUBLIC_ENDPOINTS))
        all_fields = {key for item in result if "data" in item for key in item["data"]}
        self.assertNotIn("phone", all_fields)
        self.assertNotIn("contact_email", all_fields)
        self.assertNotIn("lead_user_id", all_fields)
        self.assertNotIn("created_by", all_fields)
        self.assertNotIn("total_students", all_fields)


if __name__ == "__main__":
    unittest.main()
