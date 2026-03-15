from oilgas_indexer.utils.text_cleaner import clean_text

html = """
<html>
  <head><title>Oil India Exploration</title></head>
  <body>
    <h1>Oil and Gas Drilling Updates</h1>
    <p>Oil India Limited recently expanded operations in Assam fields.</p>
    <footer>© 2025 All rights reserved.</footer>
  </body>
</html>
"""

result = clean_text(html)
print("🧹 Cleaned Text:\n")
print(result)
