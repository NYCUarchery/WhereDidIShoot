import sys
import unittest
from pathlib import Path

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extensions import db
from app.models import Arrow, End, Practice, Round
from app.routes import api


class SoftDeleteApiTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(api)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def post(self, path, payload):
        response = self.client.post(path, json=payload)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def test_soft_delete_hides_hierarchy_without_erasing_rows(self):
        user = self.post("/api/users", {"name": "archer", "password": "secret"})
        practice = self.post("/api/practices", {"user_id": user["id"], "notes": "practice"})
        round_record = self.post(
            "/api/rounds", {"practice_id": practice["id"], "name": "round", "notes": ""}
        )
        deleted_end = self.post("/api/ends", {"round_id": round_record["id"], "notes": "first"})
        visible_end = self.post("/api/ends", {"round_id": round_record["id"], "notes": "second"})
        arrow = self.post(
            "/api/arrows",
            {
                "end_id": deleted_end["id"],
                "arrow_number": 1,
                "score": 9,
                "x": 1.25,
                "y": -2.5,
                "notes": "kept",
            },
        )
        self.assertNotIn("round_order", round_record)
        self.assertNotIn("end_number", deleted_end)
        self.assertEqual([row.id for row in db.session.get(Practice, practice["id"]).rounds], [round_record["id"]])
        self.assertEqual(
            [row.id for row in db.session.get(Round, round_record["id"]).ends],
            [deleted_end["id"], visible_end["id"]],
        )

        self.assertEqual(self.client.delete(f"/api/ends/{deleted_end['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/rounds/{round_record['id']}").get_json()["total_score"], 0)
        kept_arrow = db.session.get(Arrow, arrow["id"])
        self.assertEqual((kept_arrow.score, kept_arrow.x, kept_arrow.y, kept_arrow.notes), (9, 1.25, -2.5, "kept"))
        self.assertIsNotNone(db.session.get(End, deleted_end["id"]).deleted_at)
        for method, path in (("get", f"/api/ends/{deleted_end['id']}"), ("get", f"/api/arrows/{arrow['id']}")):
            self.assertEqual(getattr(self.client, method)(path).status_code, 404)

        self.assertEqual(self.client.delete(f"/api/practices/{practice['id']}").status_code, 204)
        self.assertIsNotNone(db.session.get(Practice, practice["id"]).deleted_at)
        self.assertIsNone(db.session.get(Round, round_record["id"]).deleted_at)
        self.assertIsNone(db.session.get(End, visible_end["id"]).deleted_at)
        for path in ("/api/practices", "/api/rounds", "/api/ends", "/api/arrows"):
            self.assertEqual(self.client.get(path).get_json(), [])
        self.assertEqual(self.client.delete(f"/api/users/{user['id']}").status_code, 409)
        other_practice = self.post("/api/practices", {"user_id": user["id"], "notes": "other"})
        for method, path, payload in (
            ("post", "/api/rounds", {"practice_id": practice["id"], "name": "blocked", "notes": ""}),
            ("post", "/api/ends", {"round_id": round_record["id"], "notes": ""}),
            ("post", "/api/arrows", {"end_id": visible_end["id"], "arrow_number": 1, "score": 1}),
            ("put", f"/api/rounds/{round_record['id']}", {"practice_id": other_practice["id"], "name": "blocked", "notes": ""}),
        ):
            self.assertEqual(getattr(self.client, method)(path, json=payload).status_code, 400 if method == "post" else 404)
        for path, payload in (
            (f"/api/practices/{practice['id']}", {"user_id": user["id"], "notes": ""}),
            (f"/api/rounds/{round_record['id']}", {"practice_id": other_practice["id"], "name": "blocked", "notes": ""}),
            (f"/api/ends/{visible_end['id']}", {"round_id": round_record["id"], "notes": ""}),
            (f"/api/arrows/{arrow['id']}", {"end_id": visible_end["id"], "arrow_number": 1, "score": 1}),
        ):
            self.assertEqual(self.client.get(path).status_code, 404)
            self.assertEqual(self.client.put(path, json=payload).status_code, 404)
            self.assertEqual(self.client.delete(path).status_code, 404)

        db.session.get(Practice, practice["id"]).deleted_at = None
        db.session.commit()
        self.assertEqual(self.client.get(f"/api/rounds/{round_record['id']}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/ends/{deleted_end['id']}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/ends/{visible_end['id']}").status_code, 200)
        transient_arrow = self.post(
            "/api/arrows", {"end_id": visible_end["id"], "arrow_number": 1, "score": 1}
        )
        self.assertEqual(self.client.delete(f"/api/arrows/{transient_arrow['id']}").status_code, 204)
        self.assertIsNone(db.session.get(Arrow, transient_arrow["id"]))

        other_round = self.post(
            "/api/rounds", {"practice_id": other_practice["id"], "name": "other", "notes": ""}
        )
        other_end = self.post("/api/ends", {"round_id": other_round["id"], "notes": "child"})
        self.assertEqual(self.client.delete(f"/api/rounds/{other_round['id']}").status_code, 204)
        self.assertIsNotNone(db.session.get(Round, other_round["id"]).deleted_at)
        self.assertIsNone(db.session.get(End, other_end["id"]).deleted_at)
        self.assertEqual(self.client.get(f"/api/ends/{other_end['id']}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
