import unittest
from ai_provider import read_api_key, enabled, allow_request, build_grounded_prompt

class TestOptionalAI(unittest.TestCase):
    def test_reads_env(self):
        self.assertEqual(read_api_key({'GEMINI_API_KEY':'secretA'}, {'GEMINI_API_KEY':'secretB'}),'secretB')
    def test_falls_back_to_streamlit_secret(self):
        self.assertEqual(read_api_key({'GEMINI_API_KEY':'secretA'}, {}),'secretA')
    def test_no_secret(self):
        self.assertEqual(read_api_key({}, {}),'')
    def test_disabled_by_default(self):
        self.assertFalse(enabled({}))
    def test_enabled_explicitly(self):
        self.assertTrue(enabled({'ENABLE_GEMINI':'true'}))
    def test_limiter(self):
        allowed, times=allow_request([100,101,102,103,104],now=110,max_per_minute=5)
        self.assertFalse(allowed)
        self.assertEqual(len(times),5)
    def test_limiter_allows(self):
        allowed,times=allow_request([],now=110)
        self.assertTrue(allowed)
        self.assertEqual(times,[110])
    def test_prompt_bounds(self):
        prompt=build_grounded_prompt('X'*900,'Y'*5000)
        self.assertIn('QUESTION:\n' + 'X'*700, prompt)
        self.assertTrue(prompt.endswith('Y'*3500))
    def test_private_note_bypass_is_ui_guarded(self):
        # AI calls in app.py are made only for RAG mode.
        self.assertIn('UNTRUSTED LESSON EXCERPTS',build_grounded_prompt('test','lesson'))
