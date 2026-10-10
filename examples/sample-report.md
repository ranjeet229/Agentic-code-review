# Reviewmate report

## HIGH: Untrusted input is executed
**app.py:3** · security · confidence 95%

`eval` executes arbitrary code supplied by the user.

Suggested fix: Parse the expected data format explicitly instead of evaluating input.
