def build_reverse_index(text):
  reverse_index = {}
  words = text.split() 

  for idx, word in enumerate(words):
      if word not in reverse_index:
          reverse_index[word] = [idx]
      else:
          reverse_index[word].append(idx)

  return reverse_index

def search_word(word, reverse_index):
  if word in reverse_index:
      return reverse_index[word]
  else:
      return []


text = "This is a simple example of a reverse index search in Python. Python is a versatile language."
reverse_index = build_reverse_index(text)

search_word_to_find = "Python"
indices = search_word(search_word_to_find, reverse_index)

if indices:
  print(f"'{search_word_to_find}' found at positions: {indices}")
else:
  print(f"'{search_word_to_find}' not found in the text.")