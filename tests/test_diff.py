from reviewmate.diff import parse_diff

SAMPLE = """diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 def run():
-    return 1
+    token = input("token: ")
+    return eval(token)
 
"""


def test_parse_diff_tracks_added_lines() -> None:
    chunks = parse_diff(SAMPLE)
    assert len(chunks) == 1
    assert chunks[0].file_path == "app.py"
    assert chunks[0].changed_lines == {2, 3}


def test_binary_diff_is_ignored() -> None:
    binary = "diff --git a/a.png b/a.png\nBinary files a/a.png and b/a.png differ\n"
    assert parse_diff(binary) == []
