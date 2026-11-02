"""HumanLang can't load one .hum file from another, so this joins the modules into library.hum, in order."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["util", "store", "members", "report", "main"]
text = "".join(open(os.path.join(HERE, m + ".hum"), encoding="utf-8").read().rstrip("\n") + "\n\n" for m in ORDER)
open(os.path.join(HERE, "library.hum"), "w", encoding="utf-8", newline="\n").write(text)
print(f"library.hum: {text.count(chr(10))} lines")
